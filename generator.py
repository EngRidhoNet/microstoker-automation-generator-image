import os
import json
import math
from datetime import datetime
from typing import List, Dict
from config import Config
from PIL import Image, ImageDraw, ImageFont
import random
import io

# Import Gemini
try:
    from google import genai
    from google.genai import types
    
    # Initialize client
    client = genai.Client(api_key=Config.GEMINI_API_KEY)
    GEMINI_AVAILABLE = True
    print("✅ Gemini Imagen client initialized successfully")
except Exception as e:
    print(f"⚠️ Gemini setup failed: {e}")
    GEMINI_AVAILABLE = False

def generate_images(keywords: List[Dict], output_dir: str) -> List[Dict]:
    """Generate images using Gemini Imagen API or fallback to placeholders"""
    
    images_dir = f"{output_dir}/images"
    os.makedirs(images_dir, exist_ok=True)
    
    generated_images = []
    
    for i, keyword_data in enumerate(keywords[:Config.DAILY_IMAGE_LIMIT]):
        keyword = keyword_data['keyword']
        category = keyword_data.get('category', 'general')
        
        filename = f"stock_{i+1:02d}_{keyword.replace(' ', '_').replace('/', '_')}.jpg"
        filepath = f"{images_dir}/{filename}"
        
        try:
            print(f"🎨 Generating image {i+1}/{Config.DAILY_IMAGE_LIMIT} for: {keyword}")
            
            # Try Gemini Imagen first
            if GEMINI_AVAILABLE:
                success = generate_with_gemini(keyword, category, filepath)
                if success:
                    image_info = {
                        'filename': filename,
                        'filepath': filepath,
                        'keyword': keyword,
                        'category': category,
                        'prompt': create_prompt(keyword, category),
                        'generated_at': datetime.now().isoformat(),
                        'file_size': os.path.getsize(filepath),
                        'status': 'ai_generated',
                        'dimensions': f"{Config.IMAGE_SIZE[0]}x{Config.IMAGE_SIZE[1]}"
                    }
                    
                    generated_images.append(image_info)
                    print(f"✅ AI image generated: {filename}")
                    
                    # Rate limiting
                    import time
                    time.sleep(2)
                    continue
            
            # Fallback to placeholder if API fails
            print(f"🔄 Creating placeholder for: {keyword}")
            create_simple_placeholder(keyword, category, filepath, i+1)
            
            image_info = {
                'filename': filename,
                'filepath': filepath,
                'keyword': keyword,
                'category': category,
                'prompt': create_prompt(keyword, category),
                'generated_at': datetime.now().isoformat(),
                'file_size': os.path.getsize(filepath),
                'status': 'placeholder_fallback',
                'dimensions': f"{Config.IMAGE_SIZE[0]}x{Config.IMAGE_SIZE[1]}"
            }
            
            generated_images.append(image_info)
            print(f"✅ Placeholder created: {filename}")
            
        except Exception as e:
            print(f"❌ Error creating image for '{keyword}': {e}")
            continue
    
    success_count = len(generated_images)
    ai_count = sum(1 for img in generated_images if img['status'] == 'ai_generated')
    placeholder_count = success_count - ai_count
    
    print(f"🎉 Successfully created {success_count} images")
    if ai_count > 0:
        print(f"   🤖 {ai_count} AI-generated images")
    if placeholder_count > 0:
        print(f"   🎨 {placeholder_count} placeholder images")
    
    return generated_images

def generate_with_gemini(keyword: str, category: str, filepath: str) -> bool:
    """Generate image using Gemini Imagen API"""
    try:
        # Create optimized prompt
        prompt = create_prompt(keyword, category)
        
        print(f"🤖 Calling Gemini API for: {keyword}")
        
        # Generate image with Gemini
        response = client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                include_rai_reason=False
            )
        )
        
        if response.generated_images and len(response.generated_images) > 0:
            # Get the generated image
            generated_image = response.generated_images[0]
            
            # Access the google.genai.types.Image object
            genai_image = generated_image.image
            
            # Debug: Let's see what attributes the Image has
            print(f"🔍 genai_image type: {type(genai_image)}")
            image_attrs = [attr for attr in dir(genai_image) if not attr.startswith('_')]
            print(f"🔍 Image attributes: {image_attrs}")
            
            # Try different ways to get image data
            pil_image = None
            
            # Method 1: Check for data attribute (bytes)
            if hasattr(genai_image, 'data'):
                try:
                    image_bytes = genai_image.data
                    print(f"🔍 Found .data attribute, type: {type(image_bytes)}")
                    if isinstance(image_bytes, bytes):
                        pil_image = Image.open(io.BytesIO(image_bytes))
                        print("✅ Successfully loaded from .data bytes")
                    else:
                        print(f"🔍 .data is not bytes: {type(image_bytes)}")
                except Exception as e:
                    print(f"🔍 Error loading from .data: {e}")
            
            # Method 2: Check for content attribute
            if pil_image is None and hasattr(genai_image, 'content'):
                try:
                    image_content = genai_image.content
                    print(f"🔍 Found .content attribute, type: {type(image_content)}")
                    if isinstance(image_content, bytes):
                        pil_image = Image.open(io.BytesIO(image_content))
                        print("✅ Successfully loaded from .content bytes")
                except Exception as e:
                    print(f"🔍 Error loading from .content: {e}")
            
            # Method 3: Check for bytes attribute
            if pil_image is None and hasattr(genai_image, 'bytes'):
                try:
                    image_bytes = genai_image.bytes
                    print(f"🔍 Found .bytes attribute, type: {type(image_bytes)}")
                    if isinstance(image_bytes, bytes):
                        pil_image = Image.open(io.BytesIO(image_bytes))
                        print("✅ Successfully loaded from .bytes")
                except Exception as e:
                    print(f"🔍 Error loading from .bytes: {e}")
            
            # Method 4: Check for url attribute (might need to download)
            if pil_image is None and hasattr(genai_image, 'url'):
                try:
                    import requests
                    image_url = genai_image.url
                    print(f"🔍 Found .url attribute: {image_url}")
                    response = requests.get(image_url)
                    if response.status_code == 200:
                        pil_image = Image.open(io.BytesIO(response.content))
                        print("✅ Successfully downloaded from .url")
                except Exception as e:
                    print(f"🔍 Error downloading from .url: {e}")
            
            # Method 5: Try to convert directly
            if pil_image is None:
                try:
                    # Maybe it has a to_pil() method or similar
                    for method_name in ['to_pil', 'as_pil', 'get_pil', 'pil_image']:
                        if hasattr(genai_image, method_name):
                            method = getattr(genai_image, method_name)
                            pil_image = method()
                            print(f"✅ Successfully converted using .{method_name}()")
                            break
                except Exception as e:
                    print(f"🔍 Error trying conversion methods: {e}")
            
            # Method 6: Check if it has a save method that we can use directly
            if pil_image is None and hasattr(genai_image, 'save'):
                try:
                    genai_image.save(filepath)
                    print("✅ Saved directly using genai_image.save()")
                    return True
                except Exception as e:
                    print(f"🔍 Error using genai_image.save(): {e}")
            
            # Method 7: Try to get raw bytes through serialization
            if pil_image is None:
                try:
                    # Maybe it has a model_dump or dict method
                    if hasattr(genai_image, 'model_dump'):
                        data_dict = genai_image.model_dump()
                        print(f"🔍 model_dump keys: {data_dict.keys()}")
                        
                        # Look for data in the dict
                        for key in ['data', 'content', 'bytes', 'image_data']:
                            if key in data_dict:
                                image_data = data_dict[key]
                                if isinstance(image_data, bytes):
                                    pil_image = Image.open(io.BytesIO(image_data))
                                    print(f"✅ Successfully loaded from model_dump['{key}']")
                                    break
                                elif isinstance(image_data, str):
                                    # Maybe it's base64 encoded
                                    import base64
                                    try:
                                        decoded_bytes = base64.b64decode(image_data)
                                        pil_image = Image.open(io.BytesIO(decoded_bytes))
                                        print(f"✅ Successfully loaded from base64 model_dump['{key}']")
                                        break
                                    except:
                                        pass
                except Exception as e:
                    print(f"🔍 Error trying model_dump: {e}")
            
            # If we successfully got a PIL image, process and save it
            if pil_image is not None:
                print(f"🔍 PIL Image size: {pil_image.size}")
                print(f"🔍 PIL Image mode: {pil_image.mode}")
                
                # Resize to our target dimensions if needed
                target_size = Config.IMAGE_SIZE
                if pil_image.size != target_size:
                    pil_image = pil_image.resize(target_size, Image.Resampling.LANCZOS)
                    print(f"🔧 Resized to {target_size}")
                
                # Convert to RGB if needed (in case it's RGBA)
                if pil_image.mode != 'RGB':
                    pil_image = pil_image.convert('RGB')
                    print(f"🔧 Converted to RGB")
                
                # Save with high quality
                pil_image.save(filepath, 'JPEG', quality=Config.IMAGE_QUALITY, optimize=True)
                print("✅ PIL Image saved successfully")
                return True
            
            print("❌ Could not extract image data from any known method")
            print("🔍 Full genai_image structure:")
            print(f"   Type: {type(genai_image)}")
            print(f"   Dir: {[attr for attr in dir(genai_image) if not attr.startswith('_')]}")
            
            # Last resort: print the object itself
            try:
                print(f"   String representation: {str(genai_image)}")
                print(f"   Repr: {repr(genai_image)}")
            except:
                pass
            
            return False
        else:
            print(f"⚠️ No images returned from API for '{keyword}'")
            return False
            
    except Exception as e:
        error_msg = str(e).lower()
        
        if "billed users" in error_msg:
            print(f"💳 Billing required for Imagen API")
        elif "unauthenticated" in error_msg:
            print(f"🔐 Authentication error - check API key")
        elif "permission denied" in error_msg:
            print(f"🔒 Permission denied - enable APIs in Google Cloud")
        elif "quota" in error_msg:
            print(f"📊 Quota exceeded")
        else:
            print(f"⚠️ API error: {str(e)[:200]}")
        
        return False

def create_simple_placeholder(keyword: str, category: str, filepath: str, number: int):
    """Create simple, reliable placeholder - no complex shapes"""
    
    # Simple category colors
    category_colors = {
        'business': {'bg': '#1E3A8A', 'accent': '#3B82F6', 'text': '#DBEAFE'},
        'technology': {'bg': '#581C87', 'accent': '#8B5CF6', 'text': '#E9D5FF'},
        'lifestyle': {'bg': '#065F46', 'accent': '#10B981', 'text': '#D1FAE5'},
        'food': {'bg': '#92400E', 'accent': '#F59E0B', 'text': '#FEF3C7'},
        'nature': {'bg': '#14532D', 'accent': '#22C55E', 'text': '#DCFCE7'},
        'general': {'bg': '#374151', 'accent': '#6B7280', 'text': '#F3F4F6'}
    }
    
    colors = category_colors.get(category, category_colors['general'])
    
    # Create image
    width, height = Config.IMAGE_SIZE
    img = Image.new('RGB', (width, height), colors['bg'])
    draw = ImageDraw.Draw(img)
    
    # Simple gradient (no complex loops)
    bg_color = colors['bg']
    accent_color = colors['accent']
    
    # Convert hex to RGB
    bg_rgb = tuple(int(bg_color[i:i+2], 16) for i in (1, 3, 5))
    accent_rgb = tuple(int(accent_color[i:i+2], 16) for i in (1, 3, 5))
    
    # Simple vertical gradient
    for y in range(height):
        ratio = y / height
        r = int(bg_rgb[0] + (accent_rgb[0] - bg_rgb[0]) * ratio * 0.3)
        g = int(bg_rgb[1] + (accent_rgb[1] - bg_rgb[1]) * ratio * 0.3)
        b = int(bg_rgb[2] + (accent_rgb[2] - bg_rgb[2]) * ratio * 0.3)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Load font safely
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 72)
        font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Center coordinates
    center_x = width // 2
    center_y = height // 2
    
    # Draw content safely
    text_color = colors['text']
    text_rgb = tuple(int(text_color[i:i+2], 16) for i in (1, 3, 5))
    
    # Title
    title = "STOCK PHOTO"
    try:
        bbox = draw.textbbox((0, 0), title, font=font_medium)
        title_width = bbox[2] - bbox[0]
    except:
        title_width = len(title) * 18
    
    draw.text((center_x - title_width//2, center_y - 80), title, fill=text_rgb, font=font_medium)
    
    # Keyword
    keyword_upper = keyword.upper()
    try:
        bbox = draw.textbbox((0, 0), keyword_upper, font=font_large)
        keyword_width = bbox[2] - bbox[0]
    except:
        keyword_width = len(keyword_upper) * 36
    
    # Simple background box for keyword
    padding = 40
    box_x1 = center_x - keyword_width//2 - padding
    box_y1 = center_y - 20
    box_x2 = center_x + keyword_width//2 + padding
    box_y2 = center_y + 60
    
    # Ensure coordinates are valid
    if box_x2 > box_x1 and box_y2 > box_y1:
        draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill=accent_rgb, outline='white', width=2)
    
    draw.text((center_x - keyword_width//2, center_y - 10), keyword_upper, fill='white', font=font_large)
    
    # Category
    category_text = f"Category: {category.title()}"
    try:
        bbox = draw.textbbox((0, 0), category_text, font=font_small)
        cat_width = bbox[2] - bbox[0]
    except:
        cat_width = len(category_text) * 12
    
    draw.text((center_x - cat_width//2, center_y + 100), category_text, fill=text_rgb, font=font_small)
    
    # Footer
    footer_text = f"Generated {datetime.now().strftime('%B %Y')} • #{number:02d}"
    draw.text((40, height - 40), footer_text, fill=text_rgb, font=font_small)
    
    specs_text = f"{width}×{height} • High Quality"
    try:
        bbox = draw.textbbox((0, 0), specs_text, font=font_small)
        specs_width = bbox[2] - bbox[0]
    except:
        specs_width = len(specs_text) * 12
    
    draw.text((width - specs_width - 40, height - 40), specs_text, fill=text_rgb, font=font_small)
    
    # Save
    img.save(filepath, 'JPEG', quality=Config.IMAGE_QUALITY, optimize=True)

def create_prompt(keyword: str, category: str) -> str:
    """Create optimized prompt for Gemini Imagen"""
    
    style_templates = {
        'business': "professional corporate stock photography, modern office environment, business meeting, clean composition",
        'technology': "cutting-edge technology stock photo, futuristic interface, clean minimalist aesthetic, innovation", 
        'lifestyle': "authentic lifestyle stock photography, natural lighting, contemporary setting, wellness focus",
        'food': "professional food stock photography, appetizing presentation, natural lighting, gourmet styling",
        'nature': "natural landscape stock photography, environmental beauty, golden hour lighting, scenic view",
        'general': "premium commercial stock photography, professional composition, studio lighting, clean background"
    }
    
    style = style_templates.get(category, style_templates['general'])
    
    # Optimized prompt for Imagen
    prompt = f"""High-quality commercial stock photograph: {keyword}. {style}. Professional photography, perfect lighting, sharp focus, commercial use ready. Clean composition without text overlays, suitable for marketing and advertising. Ultra-high resolution, professional grade."""
    
    return prompt.strip()

def test_gemini_connection():
    """Test Gemini API connection and debug image structure"""
    if not GEMINI_AVAILABLE:
        print("❌ Gemini client not available")
        return False
    
    try:
        print("🧪 Testing Gemini Imagen API...")
        
        response = client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt='A simple blue circle on white background',
            config=types.GenerateImagesConfig(number_of_images=1)
        )
        
        if response.generated_images:
            print("✅ Gemini API test successful!")
            # Debug the structure
            generated_image = response.generated_images[0]
            genai_image = generated_image.image
            
            print(f"🔍 GeneratedImage type: {type(generated_image)}")
            print(f"🔍 Image type: {type(genai_image)}")
            print(f"🔍 Image attributes: {[attr for attr in dir(genai_image) if not attr.startswith('_')]}")
            
            # Try to get more info
            if hasattr(genai_image, 'model_dump'):
                try:
                    dump = genai_image.model_dump()
                    print(f"🔍 Image model_dump keys: {list(dump.keys())}")
                except Exception as e:
                    print(f"🔍 Error getting model_dump: {e}")
            
            return True
        else:
            print("❌ No images returned from test")
            return False
            
    except Exception as e:
        error_msg = str(e).lower()
        if "billed users" in error_msg:
            print("💳 Gemini requires billing - check Google Cloud Console")
        elif "unauthenticated" in error_msg:
            print("🔐 Authentication issue - verify API key")
        elif "permission denied" in error_msg:
            print("🔒 Enable required APIs in Google Cloud Console")
        else:
            print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    # Test the system
    print("🧪 Testing Gemini Imagen generation system...")
    
    # Test API connection
    api_works = test_gemini_connection()
    
    # Test image generation
    test_keywords = [
        {'keyword': 'business meeting', 'category': 'business'}
    ]
    
    os.makedirs('test_output', exist_ok=True)
    results = generate_images(test_keywords, 'test_output')
    
    print(f"\n✅ Test completed! Generated {len(results)} images")
    
    for result in results:
        print(f"📸 {result['filename']} - {result['status']} - {result['file_size']} bytes")