# Adobe Stock Automation

Aplikasi Python untuk otomatisasi upload gambar ke Adobe Stock dengan fitur scraping trends, generasi konten otomatis, dan manajemen metadata.

## 📋 Fitur Utama

- **Scraping Trends**: Mengambil data trending topics dan keywords terbaru
- **Generasi Konten**: Membuat gambar dan konten secara otomatis berdasarkan trends
- **Metadata Management**: Pengelolaan metadata gambar untuk optimasi SEO
- **Upload Automation**: Otomatisasi proses upload ke Adobe Stock
- **Logging System**: Sistem logging untuk monitoring dan debugging

## 🚀 Instalasi

1. Clone repository ini:
```bash
git clone <repository-url>
cd adobe_stock_automation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Setup environment variables:
```bash
cp .env.example .env
```
Edit file `.env` dan isi dengan kredensial yang diperlukan.

## ⚙️ Konfigurasi

Aplikasi menggunakan file konfigurasi utama di [`config.py`](config.py). Pastikan untuk mengatur:

- API keys untuk Adobe Stock
- Path untuk direktori output
- Pengaturan scraping dan generation
- Konfigurasi logging

## 📁 Struktur Direktori

```
├── app.py              # Aplikasi utama
├── config.py           # Konfigurasi aplikasi
├── scraper.py          # Modul scraping trends
├── generator.py        # Generator konten utama
├── generator2.py       # Generator konten alternatif
├── metadata.py         # Manajemen metadata
├── output/             # Direktori hasil output
│   ├── YYYY-MM-DD/     # Output per tanggal
│   │   ├── images/     # Gambar hasil generate
│   │   ├── metadata/   # File metadata
│   │   └── upload_ready/ # File siap upload
└── enhanced_test_output/ # Output testing
```

## 🎯 Penggunaan

### Menjalankan Aplikasi Utama
```bash
python app.py
```

### Scraping Trends Data
```bash
python scraper.py
```

### Generate Konten
```bash
python generator.py
```

### Processing Metadata
```bash
python metadata.py
```

## 📊 Output

Aplikasi menghasilkan output dalam format yang terorganisir per tanggal:

- **keywords.json**: Daftar keywords trending
- **trends.json/trends_data.json**: Data trends yang telah diproses
- **images/**: Gambar yang telah digenerate
- **metadata/**: File metadata untuk setiap gambar
- **upload_ready/**: File yang siap untuk diupload
- **logs/**: Log file untuk monitoring

## 🔧 Development

### File Konfigurasi Penting

- [`.env`](.env): Environment variables (tidak di-commit ke git)
- [`.env.example`](.env.example): Template environment variables
- [`requirements.txt`](requirements.txt): Dependencies Python

### Logging

Aplikasi menggunakan logging system yang dapat ditemukan di file [`adobe_stock_automation.log`](adobe_stock_automation.log).

## 📝 Contoh Data

File [`enhanced_trends_data.json`](enhanced_trends_data.json) berisi contoh data trends yang telah diproses dan dapat digunakan untuk testing.

## 🛠️ Troubleshooting

1. **Error saat install dependencies**: Pastikan Python version kompatibel
2. **API connection issues**: Periksa konfigurasi di file `.env`
3. **Permission errors**: Pastikan direktori output memiliki permission yang sesuai

## 📄 License

[Masukkan informasi license di sini]

## 🤝 Contributing

1. Fork repository
2. Buat feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Buka Pull Request

## 📞 Support

Untuk pertanyaan atau issue, silakan buat issue di repository ini atau hubungi [ridho.aulia7324@gmail.com].