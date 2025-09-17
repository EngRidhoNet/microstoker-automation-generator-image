import json
import os
from PIL import Image
from PIL.ExifTags import TAGS
import piexif
from datetime import datetime
from typing import List, Dict
import re

def create_metadata(generated_images: List[Dict], output_dir: str):
    """Create metadata for all generated images"""
    
    metadata_dir = f"{output_dir}/metadata"
    upload_dir = f"{output_dir}/upload_ready"
    
    os.makedirs(metadata_dir, exist_ok=True)
    os.makedirs(upload_dir, exist_ok=True)
    
    print("📝 Creating metadata...")
    
    for image_info in generated_images:
        try:
            # Create individual metadata
            metadata = create_image_metadata(image_info)
            
            # Save metadata JSON
            metadata_file = f"{metadata_dir}/{image_info['filename']}.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Embed metadata into image
            embed_metadata_to_image(image_info, metadata, upload_dir)
            
            print(f"✅ Metadata created for {image_info['filename']}")
            
        except Exception as e:
            print(f"❌ Error creating metadata for {image_info['filename']}: {e}")

def create_image_metadata(image_info: Dict) -> Dict:
    """Create comprehensive metadata for Adobe Stock based on scraper data"""
    
    keyword = image_info['keyword']
    category = image_info['category']
    source = image_info.get('source', 'unknown')
    popularity = image_info.get('popularity', 75)
    
    # Generate SEO-optimized title
    title = generate_seo_title(keyword, category, popularity)
    
    # Generate description
    description = generate_description(keyword, category, source)
    
    # Generate comprehensive tags
    tags = generate_comprehensive_tags(keyword, category, source, popularity)
    
    # Generate alternative titles for A/B testing
    alternative_titles = generate_alternative_titles(keyword, category)
    
    metadata = {
        # Basic info
        'title': title,
        'description': description,
        'keywords': tags,
        'category': category,
        'subcategory': get_subcategory(keyword, category),
        
        # Rights and licensing
        'creator': 'Professional AI Photography Studio',
        'copyright': f'© {datetime.now().year} AI Stock Photography',
        'usage_rights': 'Royalty Free - Commercial Use',
        'license_type': 'Standard License',
        'model_release': False,
        'property_release': False,
        'adult_content': False,
        'editorial_use': False,
        
        # Marketing data
        'trend_data': {
            'popularity_score': popularity,
            'trending_source': source,
            'market_demand': get_market_demand(popularity),
            'seasonality': get_seasonality(keyword),
            'target_audience': get_target_audience(category)
        },
        
        # SEO optimization
        'seo_data': {
            'primary_keyword': keyword,
            'secondary_keywords': generate_secondary_keywords(keyword, category),
            'long_tail_keywords': generate_long_tail_keywords(keyword, category),
            'alternative_titles': alternative_titles,
            'search_volume': get_estimated_search_volume(popularity)
        },
        
        # Technical info
        'technical_info': {
            'software': 'Gemini Imagen 4.0',
            'ai_model': 'Google Imagen',
            'generation_date': image_info['generated_at'],
            'original_prompt': image_info.get('prompt', ''),
            'image_style': get_image_style(category),
            'color_profile': 'sRGB',
            'resolution': image_info.get('dimensions', '1600x1200'),
            'file_format': 'JPEG',
            'compression_quality': '95%'
        },
        
        # Adobe Stock specific
        'adobe_stock_metadata': {
            'content_type': 'Photo',
            'orientation': get_orientation(image_info.get('dimensions', '1600x1200')),
            'people_count': get_people_count(keyword),
            'color_composition': get_color_composition(category),
            'composition_style': get_composition_style(category),
            'mood': get_mood(keyword, category)
        }
    }
    
    return metadata

def generate_seo_title(keyword: str, category: str, popularity: int) -> str:
    """Generate SEO-optimized title based on trending data"""
    
    # High popularity gets premium descriptors
    quality_descriptor = "Premium" if popularity > 85 else "Professional" if popularity > 70 else "High Quality"
    
    title_templates = {
        'business': [
            f"{quality_descriptor} {keyword.title()} - Corporate Stock Photography",
            f"Modern {keyword.title()} Business Concept - Professional Photo",
            f"{keyword.title()} - Executive Business Stock Image"
        ],
        'technology': [
            f"Cutting-Edge {keyword.title()} - Technology Stock Photo",
            f"Modern {keyword.title()} Digital Concept - Tech Photography",
            f"Innovative {keyword.title()} - Future Technology Image"
        ],
        'lifestyle': [
            f"Authentic {keyword.title()} - Lifestyle Stock Photography",
            f"Real People {keyword.title()} - Lifestyle Concept",
            f"Contemporary {keyword.title()} - Modern Lifestyle Image"
        ],
        'food': [
            f"Gourmet {keyword.title()} - Food Photography Stock Image",
            f"Fresh {keyword.title()} - Culinary Stock Photography",
            f"Delicious {keyword.title()} - Professional Food Photo"
        ],
        'nature': [
            f"Stunning {keyword.title()} - Nature Stock Photography",
            f"Beautiful {keyword.title()} - Environmental Stock Image",
            f"Scenic {keyword.title()} - Natural Landscape Photo"
        ]
    }
    
    templates = title_templates.get(category, [f"{quality_descriptor} {keyword.title()} Stock Photo"])
    return templates[0]  # Return the first (best) template

def generate_description(keyword: str, category: str, source: str) -> str:
    """Generate detailed, marketing-focused description"""
    
    base_desc = f"Professional stock photograph featuring {keyword}."
    
    category_descriptions = {
        'business': f"{base_desc} Perfect for corporate communications, business presentations, marketing materials, and professional websites. Ideal for conveying success, teamwork, and modern business concepts.",
        
        'technology': f"{base_desc} Excellent for technology blogs, software companies, digital marketing, and innovation-focused content. Represents cutting-edge technological advancement and digital transformation.",
        
        'lifestyle': f"{base_desc} Authentic and relatable imagery perfect for lifestyle brands, wellness companies, social media, and human-centered marketing campaigns.",
        
        'food': f"{base_desc} High-quality culinary photography ideal for restaurants, food blogs, nutrition websites, cookbook covers, and food-related marketing materials.",
        
        'nature': f"{base_desc} Stunning environmental imagery perfect for travel websites, outdoor brands, environmental campaigns, and nature-focused content.",
        
        'general': f"{base_desc} Versatile stock photography suitable for various commercial applications, websites, marketing materials, and creative projects."
    }
    
    description = category_descriptions.get(category, category_descriptions['general'])
    
    # Add trending source context
    if source in ['seasonal', 'tech_trends', 'business_trends']:
        description += f" Currently trending in {source.replace('_', ' ')} markets."
    
    description += " Royalty-free license with commercial usage rights included. High resolution and professional quality guaranteed."
    
    return description

def generate_comprehensive_tags(keyword: str, category: str, source: str, popularity: int) -> List[str]:
    """Generate comprehensive tags based on scraper data"""
    
    # Start with base keyword components
    base_tags = [keyword]
    keyword_parts = re.findall(r'\b\w+\b', keyword.lower())
    base_tags.extend(keyword_parts)
    
    # Category-specific tags
    category_tags = {
        'business': [
            'business', 'corporate', 'professional', 'office', 'meeting', 'team',
            'success', 'leadership', 'strategy', 'finance', 'marketing', 'workplace',
            'executive', 'conference', 'presentation', 'collaboration', 'growth',
            'entrepreneur', 'startup', 'company', 'industry', 'commercial'
        ],
        'technology': [
            'technology', 'tech', 'digital', 'innovation', 'modern', 'computer',
            'software', 'ai', 'artificial intelligence', 'data', 'cyber', 'cloud',
            'mobile', 'internet', 'online', 'network', 'programming', 'coding',
            'future', 'automation', 'machine learning', 'blockchain', 'iot'
        ],
        'lifestyle': [
            'lifestyle', 'people', 'authentic', 'real', 'everyday', 'casual',
            'family', 'friends', 'happiness', 'wellness', 'health', 'fitness',
            'relationship', 'social', 'community', 'culture', 'leisure', 'hobby',
            'home', 'life', 'personal', 'individual', 'human', 'emotion'
        ],
        'food': [
            'food', 'cooking', 'kitchen', 'meal', 'healthy', 'nutrition', 'organic',
            'fresh', 'ingredients', 'recipe', 'chef', 'restaurant', 'dining',
            'cuisine', 'gourmet', 'delicious', 'tasty', 'culinary', 'gastronomy',
            'plate', 'dish', 'preparation', 'vegetarian', 'diet'
        ],
        'nature': [
            'nature', 'natural', 'environment', 'outdoor', 'landscape', 'scenic',
            'forest', 'mountain', 'ocean', 'sky', 'tree', 'plant', 'green',
            'sustainable', 'eco', 'wildlife', 'conservation', 'earth', 'climate',
            'season', 'weather', 'peaceful', 'serene', 'beauty', 'wilderness'
        ]
    }
    
    # Add category tags
    tags = base_tags + category_tags.get(category, [])
    
    # Add source-specific tags
    if source == 'seasonal':
        month = datetime.now().month
        seasonal_tags = {
            1: ['new year', 'winter', 'resolution', 'fresh start'],
            2: ['valentine', 'love', 'romantic', 'heart'],
            3: ['spring', 'growth', 'renewal', 'bloom'],
            4: ['easter', 'spring', 'fresh', 'new beginning'],
            5: ['mother day', 'family', 'celebration', 'flowers'],
            6: ['graduation', 'summer', 'achievement', 'success'],
            7: ['summer', 'vacation', 'freedom', 'outdoor'],
            8: ['back to school', 'education', 'learning', 'knowledge'],
            9: ['autumn', 'fall', 'harvest', 'change'],
            10: ['halloween', 'autumn', 'transformation', 'creative'],
            11: ['thanksgiving', 'gratitude', 'family', 'abundance'],
            12: ['christmas', 'holiday', 'winter', 'celebration']
        }
        tags.extend(seasonal_tags.get(month, []))
    
    elif source in ['tech_trends', 'business_trends']:
        tags.extend(['trending', 'current', 'modern', 'contemporary', 'popular'])
    
    # Add quality and usage tags
    quality_tags = [
        'stock photo', 'stock photography', 'commercial use', 'royalty free',
        'high quality', 'professional', 'hd', 'high resolution', 'premium',
        'commercial license', 'business use', 'marketing', 'advertising',
        'website', 'blog', 'social media', 'print', 'digital'
    ]
    tags.extend(quality_tags)
    
    # Add popularity-based tags
    if popularity > 90:
        tags.extend(['trending now', 'hot topic', 'viral', 'popular'])
    elif popularity > 80:
        tags.extend(['trending', 'popular', 'in demand'])
    
    # Clean and deduplicate tags
    tags = [tag.lower().strip() for tag in tags if tag and len(tag) > 1]
    tags = list(dict.fromkeys(tags))  # Remove duplicates while preserving order
    
    # Limit to 50 tags (Adobe Stock recommendation)
    return tags[:50]

def generate_secondary_keywords(keyword: str, category: str) -> List[str]:
    """Generate secondary keywords for SEO"""
    
    variations = [
        f"{keyword} photography",
        f"{keyword} image",
        f"{keyword} picture",
        f"{keyword} stock",
        f"professional {keyword}",
        f"modern {keyword}",
        f"high quality {keyword}"
    ]
    
    return variations[:5]

def generate_long_tail_keywords(keyword: str, category: str) -> List[str]:
    """Generate long-tail keywords for better SEO targeting"""
    
    long_tail = [
        f"{keyword} stock photography for commercial use",
        f"professional {keyword} images for business",
        f"royalty free {keyword} photos",
        f"high resolution {keyword} pictures",
        f"{category} {keyword} stock images"
    ]
    
    return long_tail

def generate_alternative_titles(keyword: str, category: str) -> List[str]:
    """Generate alternative titles for A/B testing"""
    
    alternatives = [
        f"Premium {keyword.title()} Stock Photo",
        f"Professional {keyword.title()} Image",
        f"High-Quality {keyword.title()} Photography",
        f"Commercial {keyword.title()} Picture",
        f"Royalty-Free {keyword.title()} Stock Image"
    ]
    
    return alternatives

def get_subcategory(keyword: str, category: str) -> str:
    """Determine subcategory based on keyword"""
    
    subcategories = {
        'business': {
            'meeting': 'Business Meetings',
            'office': 'Office Environment',
            'team': 'Teamwork',
            'finance': 'Finance & Banking',
            'marketing': 'Marketing & Advertising'
        },
        'technology': {
            'ai': 'Artificial Intelligence',
            'computer': 'Computing',
            'mobile': 'Mobile Technology',
            'data': 'Data & Analytics',
            'cyber': 'Cybersecurity'
        }
    }
    
    keyword_lower = keyword.lower()
    cat_subs = subcategories.get(category, {})
    
    for key, subcategory in cat_subs.items():
        if key in keyword_lower:
            return subcategory
    
    return category.title()

def get_market_demand(popularity: int) -> str:
    """Convert popularity score to market demand level"""
    if popularity >= 90:
        return 'Very High'
    elif popularity >= 80:
        return 'High'
    elif popularity >= 70:
        return 'Medium'
    elif popularity >= 60:
        return 'Moderate'
    else:
        return 'Low'

def get_seasonality(keyword: str) -> str:
    """Determine if keyword has seasonal relevance"""
    seasonal_keywords = {
        'spring': ['spring', 'bloom', 'growth', 'renewal'],
        'summer': ['summer', 'vacation', 'outdoor', 'beach'],
        'autumn': ['autumn', 'fall', 'harvest', 'thanksgiving'],
        'winter': ['winter', 'christmas', 'holiday', 'snow'],
        'year-round': ['business', 'technology', 'office', 'meeting']
    }
    
    keyword_lower = keyword.lower()
    for season, keywords in seasonal_keywords.items():
        if any(k in keyword_lower for k in keywords):
            return season
    
    return 'year-round'

def get_target_audience(category: str) -> str:
    """Determine target audience based on category"""
    audiences = {
        'business': 'Business professionals, marketers, corporate communications',
        'technology': 'Tech companies, startups, digital marketers, developers',
        'lifestyle': 'Lifestyle brands, wellness companies, social media marketers',
        'food': 'Restaurants, food bloggers, nutrition companies, cookbooks',
        'nature': 'Travel companies, environmental organizations, outdoor brands'
    }
    
    return audiences.get(category, 'General commercial users')

def get_estimated_search_volume(popularity: int) -> str:
    """Estimate search volume based on popularity"""
    if popularity >= 90:
        return 'High (10K+ monthly searches)'
    elif popularity >= 80:
        return 'Medium-High (5K-10K monthly searches)'
    elif popularity >= 70:
        return 'Medium (1K-5K monthly searches)'
    else:
        return 'Low-Medium (<1K monthly searches)'

def get_image_style(category: str) -> str:
    """Determine image style based on category"""
    styles = {
        'business': 'Professional, clean, corporate',
        'technology': 'Modern, sleek, futuristic',
        'lifestyle': 'Authentic, natural, relatable',
        'food': 'Appetizing, fresh, well-lit',
        'nature': 'Scenic, natural, environmental'
    }
    
    return styles.get(category, 'Professional, high-quality')

def get_orientation(dimensions: str) -> str:
    """Determine orientation from dimensions"""
    try:
        width, height = map(int, dimensions.split('x'))
        if width > height:
            return 'Landscape'
        elif height > width:
            return 'Portrait'
        else:
            return 'Square'
    except:
        return 'Landscape'

def get_people_count(keyword: str) -> int:
    """Estimate number of people in image based on keyword"""
    keyword_lower = keyword.lower()
    
    if any(word in keyword_lower for word in ['team', 'group', 'meeting', 'family']):
        return 3  # Multiple people
    elif any(word in keyword_lower for word in ['person', 'individual', 'man', 'woman', 'worker']):
        return 1  # Single person
    else:
        return 0  # No people

def get_color_composition(category: str) -> str:
    """Determine dominant color composition"""
    colors = {
        'business': 'Blue, white, gray - professional palette',
        'technology': 'Blue, white, black - modern tech palette',
        'lifestyle': 'Warm, natural tones - authentic palette',
        'food': 'Warm, appetizing colors - fresh palette',
        'nature': 'Green, blue, earth tones - natural palette'
    }
    
    return colors.get(category, 'Balanced, professional color palette')

def get_composition_style(category: str) -> str:
    """Determine composition style"""
    styles = {
        'business': 'Clean, structured, professional composition',
        'technology': 'Modern, minimalist, geometric composition',
        'lifestyle': 'Natural, candid, lifestyle composition',
        'food': 'Appetizing, well-styled, culinary composition',
        'nature': 'Scenic, environmental, landscape composition'
    }
    
    return styles.get(category, 'Professional, well-balanced composition')

def get_mood(keyword: str, category: str) -> str:
    """Determine mood/feeling of the image"""
    keyword_lower = keyword.lower()
    
    positive_words = ['success', 'happy', 'celebration', 'achievement', 'growth']
    professional_words = ['business', 'meeting', 'office', 'corporate', 'professional']
    innovative_words = ['technology', 'innovation', 'future', 'modern', 'digital']
    
    if any(word in keyword_lower for word in positive_words):
        return 'Positive, successful, uplifting'
    elif any(word in keyword_lower for word in professional_words):
        return 'Professional, confident, trustworthy'
    elif any(word in keyword_lower for word in innovative_words):
        return 'Innovative, forward-thinking, dynamic'
    else:
        return 'Professional, high-quality, commercial'

def embed_metadata_to_image(image_info: Dict, metadata: Dict, upload_dir: str):
    """Embed metadata into image file with comprehensive EXIF data"""
    
    source_path = image_info['filepath']
    target_path = f"{upload_dir}/{image_info['filename']}"
    
    try:
        # Load image
        img = Image.open(source_path)
        
        # Create comprehensive EXIF data
        exif_dict = {
            "0th": {
                piexif.ImageIFD.Artist: metadata['creator'],
                piexif.ImageIFD.Copyright: metadata['copyright'],
                piexif.ImageIFD.ImageDescription: metadata['description'][:255].encode('utf-8'),
                piexif.ImageIFD.Software: metadata['technical_info']['software'],
                piexif.ImageIFD.DocumentName: metadata['title'][:255],
            },
            "Exif": {
                piexif.ExifIFD.DateTimeOriginal: datetime.now().strftime("%Y:%m:%d %H:%M:%S"),
                piexif.ExifIFD.DateTimeDigitized: datetime.now().strftime("%Y:%m:%d %H:%M:%S"),
                piexif.ExifIFD.UserComment: f"Keywords: {', '.join(metadata['keywords'][:10])}".encode('utf-8'),
            }
        }
        
        # Convert to bytes
        exif_bytes = piexif.dump(exif_dict)
        
        # Save with embedded metadata
        img.save(target_path, "JPEG", exif=exif_bytes, quality=95, optimize=True)
        
        print(f"📎 Metadata embedded in {target_path}")
        
    except Exception as e:
        # Fallback: save without EXIF if there's an encoding issue
        print(f"⚠️ EXIF embedding failed for {image_info['filename']}, saving without EXIF: {e}")
        img = Image.open(source_path)
        img.save(target_path, "JPEG", quality=95, optimize=True)
        print(f"📎 Image saved without EXIF in {target_path}")

if __name__ == "__main__":
    # Test metadata generation
    print("🧪 Testing metadata generation...")
    
    test_image_info = {
        'filename': 'test_image.jpg',
        'filepath': 'test_path.jpg',
        'keyword': 'remote work',
        'category': 'business',
        'source': 'google_suggestions',
        'popularity': 92,
        'prompt': 'Professional remote work setup',
        'generated_at': datetime.now().isoformat(),
        'dimensions': '1600x1200'
    }
    
    metadata = create_image_metadata(test_image_info)
    
    print(f"\n📊 Generated Metadata:")
    print(f"   Title: {metadata['title']}")
    print(f"   Category: {metadata['category']} -> {metadata['subcategory']}")
    print(f"   Tags count: {len(metadata['keywords'])}")
    print(f"   Market demand: {metadata['trend_data']['market_demand']}")
    print(f"   Target audience: {metadata['trend_data']['target_audience']}")
    print(f"   Seasonality: {metadata['trend_data']['seasonality']}")
    
    print(f"\n🏷️ Sample tags: {', '.join(metadata['keywords'][:10])}")