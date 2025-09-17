#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scraper.py — Trend Scraper yang stabil untuk microstock / stock imagery.

Strategi:
1) API-first (jika tersedia): Pexels API, Unsplash API, PyTrends (Google Trends).
2) Static HTML yang server-rendered: Unsplash /t/{topic}.
3) Fallback musiman bila semua gagal: tidak pernah 0 hasil.
4) Dedup + ranking + category summary.

Env (opsional):
- PEXELS_API_KEY=<your_key>
- UNSPLASH_ACCESS_KEY=<your_key>

Jalankan:
  python scraper.py --out enhanced_trends_data.json --csv
"""

from __future__ import annotations
import os
import re
import json
import time
import math
import csv
import random
import logging
import argparse
import concurrent.futures
from datetime import datetime
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- Optional deps (safe import) ---
try:
    from pytrends.request import TrendReq  # pip install pytrends
    PYTRENDS_OK = True
except Exception:
    PYTRENDS_OK = False

# ------------- Logging -------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("trend-scraper")


# ------------- Utilities -------------
def now_iso() -> str:
    return datetime.now().isoformat()


def clamp(v: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, v))


# ------------- Core Scraper -------------
class TrendScraper:
    """
    Robust HTTP client with retries + anti-bot heuristics.
    Fokus pada sumber yang:
      - Stabil & tidak full JS (server-rendered)
      - API resmi jika tersedia
    """

    def __init__(self, timeout: int = 25):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            # Biarkan requests negosiasi Accept-Encoding (jangan paksa br)
            "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/121.0.0.0 Safari/537.36"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Upgrade-Insecure-Requests": "1",
        })
        # Simple retry (tanpa deps tambahan)
        self.retry_status = {429, 500, 502, 503, 504}

        # API keys (opsional)
        self.pexels_key = os.getenv("PEXELS_API_KEY", "").strip()
        self.unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY", "").strip()

    # ---------- HTTP fetch ----------
    def _fetch(self, url: str, max_tries: int = 3) -> Optional[BeautifulSoup]:
        for attempt in range(1, max_tries + 1):
            try:
                resp = self.session.get(url, timeout=self.timeout, allow_redirects=True)
                if resp.status_code in self.retry_status:
                    logger.info(f"[{resp.status_code}] retry {attempt}/{max_tries} {url}")
                    time.sleep(0.8 * attempt)
                    continue
                if resp.status_code != 200:
                    logger.info(f"[{resp.status_code}] {url}")
                    return None

                ct = (resp.headers.get("content-type") or "").lower()
                if "text/html" not in ct and "application/xhtml+xml" not in ct:
                    logger.debug(f"[CT={ct}] non-HTML: {url}")
                    return None

                # Anti-bot or JS shell heuristics
                head = resp.text[:2000].lower()
                if any(k in head for k in [
                    "enable javascript", "cloudflare", "akamai", "cf-chl-bypass"
                ]):
                    logger.info(f"[BOT-GUARD/JS] {url}")
                    return None

                soup = BeautifulSoup(resp.text, "html.parser")
                # minimum sanity: at least one of these exists
                if not soup.find(["a", "img", "h1", "h2", "h3"]):
                    logger.info(f"[EMPTY DOM] {url}")
                    return None

                return soup

            except requests.RequestException as e:
                logger.debug(f"_fetch error (try {attempt}/{max_tries}) {url}: {e}")
                time.sleep(0.6 * attempt)
        return None

    # ---------- Keyword utils ----------
    _STOP_WORDS = {
        'the','a','an','and','or','in','on','for','of','with','by','to','is','are',
        'stock','photo','image','images','pictures','download','free','hd'
    }

    def _extract_keywords(self, text: str, hard_cap: int = 200) -> List[str]:
        """
        Ekstraksi kata/phrase (allow digits). Pertahankan -, &, / (berguna utk istilah).
        """
        if not text:
            return []
        text = re.sub(r'[^\w\s\-\&/]', ' ', text.lower())
        text = re.sub(r'\s+', ' ', text).strip()
        if not text:
            return []

        toks = [t for t in text.split() if t not in self._STOP_WORDS and len(t) >= 2]
        out = set(toks)

        # bi-grams
        for i in range(len(toks) - 1):
            w1, w2 = toks[i], toks[i + 1]
            if w1 not in self._STOP_WORDS and w2 not in self._STOP_WORDS:
                out.add(f"{w1} {w2}")

        # tri-grams
        for i in range(len(toks) - 2):
            w1, w2, w3 = toks[i:i + 3]
            if all(w not in self._STOP_WORDS for w in (w1, w2, w3)):
                phrase = f"{w1} {w2} {w3}"
                if 3 <= len(phrase) <= 40:
                    out.add(phrase)

        res = list(out)
        random.shuffle(res)
        return res[:hard_cap]

    def _categorize(self, keyword: str) -> str:
        k = keyword.lower()
        def anyin(xs): return any(t in k for t in xs)
        if anyin(['ai','artificial','machine learning','ml','blockchain','saas','api','cloud','vr','ar','3d','data']):
            return 'technology'
        if anyin(['business','corporate','office','startup','strategy','marketing','revenue','meeting']):
            return 'business'
        if anyin(['medical','health','healthcare','doctor','nurse','patient','therapy','vaccine','fitness','wellness']):
            return 'medical'
        if anyin(['education','school','student','teacher','university','learning','research']):
            return 'education'
        if anyin(['food','cuisine','cooking','meal','recipe','kitchen','coffee','tea','restaurant','diet','vegan','plant']):
            return 'food'
        if anyin(['nature','forest','mountain','ocean','sea','beach','sky','wildlife','green','sustainable','climate']):
            return 'nature'
        if anyin(['lifestyle','family','people','beauty','fashion','home','interior','yoga','meditation']):
            return 'lifestyle'
        return 'general'

    def _score(self, keyword: str, source: str) -> int:
        base = {
            'pexels_api': 85,
            'unsplash_api': 84,
            'unsplash_topics': 78,
            'pytrends': 88,
            'seasonal': 72,
        }.get(source, 70)

        kl = keyword.lower()
        if any(t in kl for t in ['ai','artificial intelligence','machine learning','3d']):
            base += 8
        elif any(t in kl for t in ['sustainable','green','eco','renewable']):
            base += 6
        elif any(t in kl for t in ['remote work','digital transformation','hybrid']):
            base += 6
        elif any(t in kl for t in ['health','wellness','mental health']):
            base += 5
        elif any(t in kl for t in ['diversity','inclusion']):
            base += 4

        # bonus untuk 2-3 kata
        wc = len(keyword.split())
        if wc == 2:
            base += 3
        elif wc == 3:
            base += 2

        # penalty untuk phrase sangat panjang
        if len(keyword) > 40:
            base -= 6
        elif len(keyword) > 30:
            base -= 3

        return clamp(base + random.randint(-2, 2), 50, 99)

    # ---------- Sources ----------
    def source_pexels_api(self, limit_terms: int = 30) -> List[Dict]:
        """
        Pexels API: pakai endpoint search populer via iterasi seed.
        Catatan: Pexels tidak expose 'trending' langsung, tapi kita bisa
        memanen suggestion/popular via beberapa seed query umum.
        """
        if not self.pexels_key:
            return []
        headers = {"Authorization": self.pexels_key}
        base = "https://api.pexels.com/v1/search"
        seeds = ["business", "technology", "nature", "people", "food", "education", "medical", "startup", "ai"]
        trends: List[Dict] = []

        for q in seeds:
            try:
                params = {"query": q, "per_page": 1}  # kita tidak butuh gambar, hanya meta
                r = requests.get(base, headers=headers, params=params, timeout=self.timeout)
                if r.status_code != 200:
                    logger.debug(f"Pexels API [{r.status_code}] {q}")
                    continue
                data = r.json()
                # Ambil terms dari url next_page/prev_page atau query normalisasi
                # plus tambahkan variasi seed sebagai keyword
                kws = {q}
                # Dari hasil photo(s), ambil tags (jika ada)
                for ph in data.get("photos", []):
                    alt = (ph.get("alt") or "").strip().lower()
                    kws.update(self._extract_keywords(alt, hard_cap=20))
                for kw in list(kws)[:5]:
                    trends.append({
                        "keyword": kw,
                        "popularity": self._score(kw, "pexels_api"),
                        "category": self._categorize(kw),
                        "source": "pexels_api"
                    })
                time.sleep(0.3)
            except Exception as e:
                logger.debug(f"Pexels API error for seed '{q}': {e}")

        random.shuffle(trends)
        return trends[:limit_terms]

    def source_unsplash_api_or_topics(self, limit_terms: int = 30) -> List[Dict]:
        """
        Jika ada UNSPLASH_ACCESS_KEY → gunakan API.
        Jika tidak ada → scrape topic pages (server-rendered, stabil).
        """
        if self.unsplash_key:
            return self._unsplash_api(limit_terms=limit_terms)
        else:
            return self._unsplash_topics_html(limit_terms=limit_terms)

    def _unsplash_api(self, limit_terms: int = 30) -> List[Dict]:
        """
        Unsplash API: gunakan beberapa topik & query populer untuk memanen alt/desc.
        """
        base = "https://api.unsplash.com/search/photos"
        headers = {"Accept-Version": "v1", "Authorization": f"Client-ID {self.unsplash_key}"}
        seeds = ["business", "technology", "ai", "people", "portrait", "education", "healthy food", "nature", "3d render"]
        trends: List[Dict] = []

        for q in seeds:
            try:
                params = {"query": q, "per_page": 5}
                r = requests.get(base, headers=headers, params=params, timeout=self.timeout)
                if r.status_code != 200:
                    logger.debug(f"Unsplash API [{r.status_code}] {q}")
                    continue
                data = r.json()
                kws = {q}
                for it in data.get("results", []):
                    alt = (it.get("alt_description") or "").strip().lower()
                    desc = (it.get("description") or "").strip().lower()
                    kws.update(self._extract_keywords(alt, 30))
                    kws.update(self._extract_keywords(desc, 30))
                for kw in list(kws)[:6]:
                    trends.append({
                        "keyword": kw,
                        "popularity": self._score(kw, "unsplash_api"),
                        "category": self._categorize(kw),
                        "source": "unsplash_api"
                    })
                time.sleep(0.25)
            except Exception as e:
                logger.debug(f"Unsplash API error {q}: {e}")

        random.shuffle(trends)
        return trends[:limit_terms]

    def _unsplash_topics_html(self, limit_terms: int = 30) -> List[Dict]:
        """
        Unsplash Topic pages (server-rendered):
          https://unsplash.com/t/nature, /t/business-work, /t/people, dll.
        """
        urls = [
            "https://unsplash.com/t/nature",
            "https://unsplash.com/t/business-work",
            "https://unsplash.com/t/people",
            "https://unsplash.com/t/wallpapers",
            "https://unsplash.com/t/technology",
            "https://unsplash.com/t/architecture-interior",
        ]
        trends: List[Dict] = []
        for url in urls:
            soup = self._fetch(url)
            if not soup:
                continue

            # Ambil judul/anchor yang biasanya SEO-friendly
            selectors = [
                "h1", "h2", "h3",
                "a[title]", 'a[href*="/s/photos/"]'
            ]
            kws = set()
            for sel in selectors:
                for el in soup.select(sel):
                    text = (el.get("title") or el.get_text(strip=True) or "").lower()
                    kws.update(self._extract_keywords(text, 50))

            for kw in list(kws)[:10]:
                trends.append({
                    "keyword": kw,
                    "popularity": self._score(kw, "unsplash_topics"),
                    "category": self._categorize(kw),
                    "source": "unsplash_topics",
                })
            time.sleep(0.5)

        # batasi output
        random.shuffle(trends)
        return trends[:limit_terms]

    def source_pytrends(self, limit_terms: int = 30) -> List[Dict]:
        """
        Google Trends via pytrends (jika tersedia).
        Ambil rising queries untuk sejumlah seed topics.
        """
        if not PYTRENDS_OK:
            return []

        trends: List[Dict] = []
        try:
            # PyTrends session; hl=id-ID bisa disesuaikan
            pt = TrendReq(hl='en-US', tz=420)  # Asia/Jakarta UTC+7 → tz=420
            seeds = ["artificial intelligence", "business", "healthy food", "nature", "education", "wellness", "3d render"]
            for kw in seeds:
                try:
                    pt.build_payload([kw], timeframe='now 7-d', geo="")  # global 7 hari
                    related = pt.related_queries()
                    # related format: {kw: {'top': df, 'rising': df}}
                    rising = related.get(kw, {}).get('rising')
                    if rising is not None and not rising.empty:
                        for _, row in rising.head(6).iterrows():
                            key = str(row.get('query') or '').strip().lower()
                            if not key:
                                continue
                            for k in self._extract_keywords(key, 10):
                                trends.append({
                                    "keyword": k,
                                    "popularity": self._score(k, "pytrends"),
                                    "category": self._categorize(k),
                                    "source": "pytrends",
                                })
                    time.sleep(0.4)
                except Exception as e:
                    logger.debug(f"pytrends seed error '{kw}': {e}")
        except Exception as e:
            logger.debug(f"pytrends init error: {e}")
            return []

        random.shuffle(trends)
        return trends[:limit_terms]

    def source_seasonal(self) -> List[Dict]:
        """Seasonal baseline supaya tidak pernah 0 hasil."""
        now = datetime.now()
        month = now.month
        season_names = ["winter", "spring", "summer", "autumn"]
        season = season_names[((month - 1) // 3) % 4]

        buckets = ["business", "lifestyle", "nature", "technology", "food", "education"]
        trends: List[Dict] = []
        for b in buckets:
            kw = f"{season} {b}"
            trends.append({
                "keyword": kw,
                "popularity": random.randint(70, 88),
                "category": self._categorize(kw),
                "source": "seasonal",
            })
        return trends

    # ---------- Orchestrator ----------
    def collect(self, max_workers: int = 3) -> Dict:
        start = time.time()
        all_trends: List[Dict] = []
        used_sources: List[str] = []

        sources = [
            ("pexels_api", self.source_pexels_api),
            ("unsplash", self.source_unsplash_api_or_topics),
            ("pytrends", self.source_pytrends),
        ]

        # concurrency dengan guard waktu longgar
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
            futs = {ex.submit(fn): name for name, fn in sources}
            for fut in concurrent.futures.as_completed(futs, timeout=180):
                name = futs[fut]
                try:
                    res = fut.result(timeout=60)
                    if res:
                        all_trends.extend(res)
                        used_sources.append(name)
                        logger.info(f"Source '{name}' → {len(res)} trends")
                    else:
                        logger.info(f"Source '{name}' → no data")
                except concurrent.futures.TimeoutError:
                    logger.error(f"Timeout source '{name}'")
                except Exception as e:
                    logger.error(f"Error source '{name}': {e}")

        # Tambahkan seasonal baseline selalu (tapi akan disaring saat ranking)
        seasonals = self.source_seasonal()
        all_trends.extend(seasonals)
        if "seasonal" not in used_sources:
            used_sources.append("seasonal")

        # Dedup + pilih varian terbaik per keyword
        unique: Dict[str, Dict] = {}
        source_priority = {
            'pytrends': 9,
            'pexels_api': 8,
            'unsplash_api': 7,
            'unsplash_topics': 6,
            'seasonal': 4,
        }

        for t in all_trends:
            kw = t["keyword"].strip().lower()
            if not (3 <= len(kw) <= 50):
                continue
            # filter noise yang jelas (misal underscore panjang)
            if re.search(r'_{2,}', kw):
                continue

            if kw not in unique:
                unique[kw] = t
            else:
                cur = unique[kw]
                cp = source_priority.get(cur.get("source", ""), 0)
                np_ = source_priority.get(t.get("source", ""), 0)
                if (t["popularity"] > cur["popularity"]) or (
                    t["popularity"] == cur["popularity"] and np_ > cp
                ):
                    unique[kw] = t

        # Ranking: popularity desc, lalu phrase lebih spesifik (lebih banyak kata)
        ranked = sorted(
            unique.values(),
            key=lambda x: (x["popularity"], len(x["keyword"].split())),
            reverse=True
        )

        top_trends = ranked[:20]

        # Build category summary
        categories: Dict[str, Dict] = {}
        for tr in top_trends:
            cat = tr["category"]
            c = categories.setdefault(cat, {
                "name": cat.title(),
                "count": 0,
                "avg_popularity": 0.0,
                "total_popularity": 0,
                "top_keywords": []
            })
            c["count"] += 1
            c["total_popularity"] += int(tr["popularity"])
            c["top_keywords"].append({"keyword": tr["keyword"], "popularity": tr["popularity"]})

        for c in categories.values():
            c["avg_popularity"] = c["total_popularity"] / max(1, c["count"])
            c["top_keywords"] = sorted(c["top_keywords"], key=lambda x: x["popularity"], reverse=True)[:5]
            del c["total_popularity"]

        data = {
            "scrape_date": now_iso(),
            "scraping_duration": round(time.time() - start, 2),
            "sources_used": used_sources,
            "total_keywords_found": len(all_trends),
            "trending_searches": top_trends,
            "popular_categories": sorted(categories.values(), key=lambda x: x["avg_popularity"], reverse=True),
            # Seasonal items that lolos ke top_trends (opsional, bisa ditampilkan terpisah)
            "seasonal_trends": [t for t in top_trends if t["source"] == "seasonal"]
        }
        return data


# ------------- CLI -------------
def save_json(path: str, data: Dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved JSON → {path}")


def save_csv(path: str, trends: List[Dict]):
    cols = ["keyword", "popularity", "category", "source"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for t in trends:
            w.writerow({k: t.get(k, "") for k in cols})
    logger.info(f"Saved CSV → {path}")


def main():
    ap = argparse.ArgumentParser(description="Robust Trend Scraper")
    ap.add_argument("--out", type=str, default="enhanced_trends_data.json", help="Output JSON path")
    ap.add_argument("--csv", action="store_true", help="Also write CSV next to JSON")
    args = ap.parse_args()

    scraper = TrendScraper()
    data = scraper.collect(max_workers=3)

    # Pretty print
    print("\n📊 Enhanced Scraping Results:")
    print(f"   📅 Date: {data['scrape_date']}")
    print(f"   ⏱️ Duration: {data['scraping_duration']} seconds")
    print(f"   🔍 Sources used: {', '.join(data['sources_used'])}")
    print(f"   📈 Total raw trends found: {data['total_keywords_found']}")
    print(f"   🎯 Unique trends selected: {len(data['trending_searches'])}\n")

    print("🏆 Top Trending Keywords:")
    for i, tr in enumerate(data["trending_searches"][:15], 1):
        print(f"   {i:2d}. {tr['keyword'][:32]:32s} | {tr['popularity']:3d}% | {tr['category']:10s} | {tr['source']}")

    save_json(args.out, data)
    if args.csv:
        base, _ = os.path.splitext(args.out)
        save_csv(base + ".csv", data["trending_searches"])


if __name__ == "__main__":
    main()


# --- Backward-compatible wrappers for app.py ---
def scrape_adobe_trends():
    """Maintain old interface expected by app.py"""
    scraper = TrendScraper()
    return scraper.collect(max_workers=3)

def scrape_trending_searches(headers=None):
    data = scrape_adobe_trends()
    return data.get("trending_searches", [])

def scrape_popular_categories(headers=None):
    data = scrape_adobe_trends()
    return data.get("popular_categories", [])
