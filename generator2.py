import os
import json
import math
from datetime import datetime
from typing import List, Dict
from config import Config
from PIL import Image, ImageDraw, ImageFont
import random
import io
import time

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
    
    print(f"🎨 Generating {len(keywords[:Config.DAILY_IMAGE_LIMIT])} images...")
    
    for i, keyword_data in enumerate(keywords[:Config.DAILY_IMAGE_LIMIT]):
        keyword = keyword_data['keyword']
        category = keyword_data.get('category', 'general')
        popularity = keyword_data.get('popularity', 75)
        source = keyword_data.get('source', 'unknown')
        
        # Safe filename generation
        safe_keyword = keyword.replace(' ', '_').replace('/', '_').replace('\\', '_')
        safe_keyword = ''.join(c for c in safe_keyword if c.isalnum() or c in ['_', '-'])
        filename = f"stock_{i+1:02d}_{safe_keyword}.jpg"
        filepath = f"{images_dir}/{filename}"
        
        try:
            print(f"🎨 Generating image {i+1}/{Config.DAILY_IMAGE_LIMIT} for: {keyword}")
            print(f"   📊 Popularity: {popularity}% | Category: {category} | Source: {source}")
            
            # Try Gemini Imagen first
            success = False
            if GEMINI_AVAILABLE:
                success = generate_with_gemini(keyword, category, filepath, popularity)
                
                if success:
                    image_info = {
                        'filename': filename,
                        'filepath': filepath,
                        'keyword': keyword,
                        'category': category,
                        'popularity': popularity,
                        'source': source,
                        'prompt': create_prompt(keyword, category, popularity),
                        'generated_at': datetime.now().isoformat(),
                        'file_size': os.path.getsize(filepath),
                        'status': 'ai_generated',
                        'dimensions': f"{Config.IMAGE_SIZE[0]}x{Config.IMAGE_SIZE[1]}",
                        'generation_method': 'gemini_imagen'
                    }
                    
                    generated_images.append(image_info)
                    print(f"✅ AI image generated: {filename}")
                    
                    # Rate limiting for API
                    time.sleep(2)
                    continue
            
            # Fallback to placeholder if API fails or unavailable
            print(f"🔄 Creating professional placeholder for: {keyword}")
            create_professional_placeholder(keyword, category, filepath, i+1, popularity, source)
            
            image_info = {
                'filename': filename,
                'filepath': filepath,
                'keyword': keyword,
                'category': category,
                'popularity': popularity,
                'source': source,
                'prompt': create_prompt(keyword, category, popularity),
                'generated_at': datetime.now().isoformat(),
                'file_size': os.path.getsize(filepath),
                'status': 'professional_placeholder',
                'dimensions': f"{Config.IMAGE_SIZE[0]}x{Config.IMAGE_SIZE[1]}",
                'generation_method': 'placeholder_ai_styled'
            }
            
            generated_images.append(image_info)
            print(f"✅ Professional placeholder created: {filename}")
            
        except Exception as e:
            print(f"❌ Error creating image for '{keyword}': {e}")
            continue
    
    # Summary
    success_count = len(generated_images)
    ai_count = sum(1 for img in generated_images if img['status'] == 'ai_generated')
    placeholder_count = success_count - ai_count
    
    print(f"\n🎉 Image generation completed!")
    print(f"   📊 Total images: {success_count}")
    if ai_count > 0:
        print(f"   🤖 AI-generated: {ai_count}")
    if placeholder_count > 0:
        print(f"   🎨 Professional placeholders: {placeholder_count}")
    
    return generated_images

def generate_with_gemini(keyword: str, category: str, filepath: str, popularity: int) -> bool:
    """Generate image using Gemini Imagen API with enhanced debugging and extraction"""
    try:
        # Create optimized prompt based on popularity and category
        prompt = create_prompt(keyword, category, popularity)
        
        print(f"🤖 Calling Gemini API for: {keyword}")
        print(f"   📝 Prompt: {prompt[:80]}...")
        
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
            genai_image = generated_image.image
            
            print(f"🔍 Debug: Response structure analysis")
            print(f"   Response type: {type(response)}")
            print(f"   Generated images count: {len(response.generated_images)}")
            print(f"   Generated image type: {type(generated_image)}")
            print(f"   GenAI image type: {type(genai_image)}")
            
            # Debug: Show all available attributes
            available_attrs = [attr for attr in dir(genai_image) if not attr.startswith('_')]
            print(f"   Available attributes: {available_attrs}")
            
            # Try different extraction methods with detailed debugging
            pil_image = None
            
            # Method 1: Direct data attribute
            if hasattr(genai_image, 'data'):
                try:
                    image_bytes = genai_image.data
                    print(f"🔍 Method 1 - Direct .data:")
                    print(f"   Data type: {type(image_bytes)}")
                    print(f"   Data length: {len(image_bytes) if hasattr(image_bytes, '__len__') else 'Unknown'}")
                    
                    if isinstance(image_bytes, bytes):
                        pil_image = Image.open(io.BytesIO(image_bytes))
                        print("✅ Successfully loaded from .data bytes")
                    elif isinstance(image_bytes, str):
                        # Try base64 decode
                        import base64
                        try:
                            decoded_bytes = base64.b64decode(image_bytes)
                            pil_image = Image.open(io.BytesIO(decoded_bytes))
                            print("✅ Successfully loaded from base64 .data")
                        except Exception as decode_error:
                            print(f"❌ Base64 decode failed: {decode_error}")
                    else:
                        print(f"❌ Unexpected data type: {type(image_bytes)}")
                except Exception as e:
                    print(f"❌ Error accessing .data: {e}")
            
            # Method 2: Check if it's a bytes-like object itself
            if pil_image is None:
                try:
                    print(f"🔍 Method 2 - Direct image object:")
                    if isinstance(genai_image, bytes):
                        pil_image = Image.open(io.BytesIO(genai_image))
                        print("✅ Successfully loaded from direct bytes")
                    else:
                        print(f"❌ Image is not bytes: {type(genai_image)}")
                except Exception as e:
                    print(f"❌ Error with direct bytes: {e}")
            
            # Method 3: Try model_dump or dict conversion
            if pil_image is None and hasattr(genai_image, 'model_dump'):
                try:
                    print(f"🔍 Method 3 - model_dump:")
                    data_dict = genai_image.model_dump()
                    print(f"   Model dump keys: {list(data_dict.keys()) if isinstance(data_dict, dict) else 'Not a dict'}")
                    
                    if isinstance(data_dict, dict):
                        for key in ['data', 'content', 'bytes', 'image_data', 'image_bytes']:
                            if key in data_dict:
                                image_data = data_dict[key]
                                print(f"   Found key '{key}' with type: {type(image_data)}")
                                
                                if isinstance(image_data, bytes):
                                    pil_image = Image.open(io.BytesIO(image_data))
                                    print(f"✅ Successfully loaded from model_dump['{key}']")
                                    break
                                elif isinstance(image_data, str):
                                    # Try base64 decode
                                    import base64
                                    try:
                                        decoded_bytes = base64.b64decode(image_data)
                                        pil_image = Image.open(io.BytesIO(decoded_bytes))
                                        print(f"✅ Successfully loaded from base64 model_dump['{key}']")
                                        break
                                    except Exception as decode_error:
                                        print(f"❌ Base64 decode failed for {key}: {decode_error}")
                                        continue
                except Exception as e:
                    print(f"❌ Error with model_dump: {e}")
            
            # Method 4: Try to access response object directly
            if pil_image is None:
                try:
                    print(f"🔍 Method 4 - Response object exploration:")
                    
                    # Try accessing the response object itself
                    response_attrs = [attr for attr in dir(response) if not attr.startswith('_')]
                    print(f"   Response attributes: {response_attrs}")
                    
                    # Check if response has any binary data
                    for attr in ['data', 'content', 'bytes']:
                        if hasattr(response, attr):
                            attr_value = getattr(response, attr)
                            print(f"   Response.{attr}: {type(attr_value)}")
                            
                except Exception as e:
                    print(f"❌ Error exploring response: {e}")
            
            # Method 5: Try using str() or repr() to see actual content
            if pil_image is None:
                try:
                    print(f"🔍 Method 5 - String representation analysis:")
                    image_str = str(genai_image)[:200]  # First 200 chars
                    print(f"   Image string repr: {image_str}")
                    
                    # Look for base64 patterns
                    if 'data:image' in image_str:
                        # Data URL format
                        if 'base64,' in image_str:
                            base64_data = image_str.split('base64,')[1]
                            import base64
                            try:
                                decoded_bytes = base64.b64decode(base64_data)
                                pil_image = Image.open(io.BytesIO(decoded_bytes))
                                print("✅ Successfully loaded from data URL")
                            except Exception as decode_error:
                                print(f"❌ Data URL decode failed: {decode_error}")
                    
                except Exception as e:
                    print(f"❌ Error with string analysis: {e}")
            
            # Method 6: Try using the Google genai client's built-in methods
            if pil_image is None:
                try:
                    print(f"🔍 Method 6 - Built-in methods:")
                    
                    # Check for save method
                    if hasattr(genai_image, 'save'):
                        print("   Found .save() method")
                        temp_path = f"{filepath}.temp"
                        genai_image.save(temp_path)
                        pil_image = Image.open(temp_path)
                        os.remove(temp_path)  # Clean up
                        print("✅ Successfully loaded using .save() method")
                    
                    # Check for show method (might give us access to data)
                    elif hasattr(genai_image, 'show'):
                        print("   Found .show() method - not suitable for extraction")
                    
                except Exception as e:
                    print(f"❌ Error with built-in methods: {e}")
            
            # If we got a PIL image, process and save it
            if pil_image is not None:
                print(f"🔍 Original image: {pil_image.size}, mode: {pil_image.mode}")
                
                # Resize to target dimensions
                target_size = Config.IMAGE_SIZE
                if pil_image.size != target_size:
                    pil_image = pil_image.resize(target_size, Image.Resampling.LANCZOS)
                    print(f"🔧 Resized to {target_size}")
                
                # Convert to RGB if needed
                if pil_image.mode != 'RGB':
                    pil_image = pil_image.convert('RGB')
                    print(f"🔧 Converted to RGB")
                
                # Save with high quality
                pil_image.save(filepath, 'JPEG', quality=Config.IMAGE_QUALITY, optimize=True)
                print("✅ Gemini image saved successfully")
                return True
            else:
                print("❌ All extraction methods failed - could not get image data")
                
                # Final debug: Try to get any useful information
                print(f"🔍 Final debug info:")
                try:
                    print(f"   genai_image.__dict__: {getattr(genai_image, '__dict__', 'No __dict__')}")
                except:
                    pass
                
                return False
        else:
            print(f"⚠️ No images returned from API for '{keyword}'")
            return False
            
    except Exception as e:
        error_msg = str(e).lower()
        
        if "billed users" in error_msg:
            print(f"💳 Billing required for Imagen API - check Google Cloud Console")
        elif "unauthenticated" in error_msg:
            print(f"🔐 Authentication error - verify API key in config")
        elif "permission denied" in error_msg:
            print(f"🔒 Permission denied - enable Imagen API in Google Cloud")
        elif "quota" in error_msg:
            print(f"📊 API quota exceeded - check usage limits")
        elif "safety" in error_msg:
            print(f"🛡️ Content filtered by safety policies")
        else:
            print(f"⚠️ API error: {str(e)[:150]}")
            print(f"🔍 Full error: {e}")
        
        return False

def test_gemini_connection():
    """Test Gemini API connection with comprehensive debugging"""
    if not GEMINI_AVAILABLE:
        print("❌ Gemini client not available")
        return False
    
    try:
        print("🧪 Testing Gemini Imagen API connection with detailed debugging...")
        
        # Use a very simple prompt to minimize safety issues
        test_prompt = "A simple blue geometric shape on white background"
        
        print(f"📝 Test prompt: {test_prompt}")
        
        response = client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt=test_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                include_rai_reason=False
            )
        )
        
        print(f"✅ API call successful!")
        print(f"🔍 Response type: {type(response)}")
        
        if hasattr(response, 'generated_images'):
            print(f"📊 Generated images count: {len(response.generated_images)}")
            
            if response.generated_images:
                generated_image = response.generated_images[0]
                genai_image = generated_image.image
                
                print(f"🔍 Response structure analysis:")
                print(f"   GeneratedImage type: {type(generated_image)}")
                print(f"   Image type: {type(genai_image)}")
                
                # Show available methods and attributes
                image_attrs = [attr for attr in dir(genai_image) if not attr.startswith('_')]
                response_attrs = [attr for attr in dir(response) if not attr.startswith('_')]
                generated_attrs = [attr for attr in dir(generated_image) if not attr.startswith('_')]
                
                print(f"   Image attributes: {image_attrs[:10]}...")  # First 10
                print(f"   Response attributes: {response_attrs[:10]}...")  # First 10
                print(f"   Generated attributes: {generated_attrs[:10]}...")  # First 10
                
                # Try to determine what we're working with
                if hasattr(genai_image, 'data'):
                    data_type = type(genai_image.data)
                    print(f"   genai_image.data type: {data_type}")
                    
                    if hasattr(genai_image.data, '__len__'):
                        print(f"   genai_image.data length: {len(genai_image.data)}")
                
                return True
            else:
                print("❌ No images in response.generated_images")
                return False
        else:
            print("❌ No generated_images attribute in response")
            print(f"🔍 Response attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
            return False
            
    except Exception as e:
        error_msg = str(e).lower()
        print(f"❌ API test failed with error: {e}")
        
        if "billed users" in error_msg:
            print("💳 Gemini requires billing - enable in Google Cloud Console")
            print("🔗 Go to: https://console.cloud.google.com/billing")
        elif "unauthenticated" in error_msg:
            print("🔐 Authentication failed - check API key configuration")
            print(f"🔑 Current API key: {Config.GEMINI_API_KEY[:10] if Config.GEMINI_API_KEY else 'Not set'}...")
        elif "permission denied" in error_msg:
            print("🔒 Permission denied - enable Imagen API in Google Cloud")
            print("🔗 Go to: https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com")
        elif "quota" in error_msg:
            print("📊 API quota exceeded - check usage limits")
        else:
            print(f"🔍 Full error details: {e}")
        
        return False

# Add a simple debug function to explore the response structure
def debug_gemini_response():
    """Debug function to explore Gemini response structure"""
    if not GEMINI_AVAILABLE:
        print("❌ Gemini client not available")
        return
    
    try:
        print("🔍 Debugging Gemini response structure...")
        
        response = client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt='A simple red circle',
            config=types.GenerateImagesConfig(number_of_images=1)
        )
        
        print(f"📊 Full response structure:")
        print(f"   Type: {type(response)}")
        print(f"   Dir: {[attr for attr in dir(response) if not attr.startswith('_')]}")
        
        if hasattr(response, 'generated_images') and response.generated_images:
            gen_img = response.generated_images[0]
            print(f"\n📊 GeneratedImage structure:")
            print(f"   Type: {type(gen_img)}")
            print(f"   Dir: {[attr for attr in dir(gen_img) if not attr.startswith('_')]}")
            
            if hasattr(gen_img, 'image'):
                img = gen_img.image
                print(f"\n📊 Image object structure:")
                print(f"   Type: {type(img)}")
                print(f"   Dir: {[attr for attr in dir(img) if not attr.startswith('_')]}")
                
                # Try to access each attribute
                for attr in dir(img):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(img, attr)
                            print(f"   {attr}: {type(value)} - {str(value)[:50]}...")
                        except Exception as e:
                            print(f"   {attr}: Error accessing - {e}")
    
    except Exception as e:
        print(f"❌ Debug failed: {e}")

if __name__ == "__main__":
    print("🧪 Enhanced Gemini debugging...")
    
    # First, run the debug function
    debug_gemini_response()
    
    print("\n" + "="*50)
    
    # Then test normal connection
    api_works = test_gemini_connection()
    
    if api_works:
        print("\n🎯 API works! Let's try generating a test image...")
        
        # Test actual generation
        test_keywords = [
            {
                'keyword': 'simple geometric shape',
                'category': 'general',
                'popularity': 75,
                'source': 'test'
            }
        ]
        
        os.makedirs('debug_output', exist_ok=True)
        results = generate_images(test_keywords, 'debug_output')
        
        print(f"\n📊 Debug results:")
        for result in results:
            print(f"   {result['filename']}: {result['status']} ({result['generation_method']})")
    else:
        print("\n❌ API connection failed - check configuration")

def create_professional_placeholder(keyword: str, category: str, filepath: str, number: int, popularity: int, source: str):
    """Create professional-grade placeholder that looks like real stock photos"""
    
    # Enhanced category designs based on real market data
    category_designs = {
        'business': {
            'gradients': [
                ['#0F172A', '#1E293B', '#334155', '#475569', '#64748B'],  # Slate
                ['#1E40AF', '#3B82F6', '#60A5FA', '#93C5FD', '#DBEAFE']   # Blue
            ],
            'accent': '#3B82F6',
            'secondary': '#60A5FA',
            'icon': '💼',
            'theme': 'BUSINESS EXCELLENCE',
            'subtitle': f'Corporate • Professional • {get_trend_indicator(popularity, source)}'
        },
        'technology': {
            'gradients': [
                ['#1E1B4B', '#3730A3', '#4F46E5', '#6366F1', '#818CF8'],  # Indigo
                ['#7C3AED', '#8B5CF6', '#A78BFA', '#C4B5FD', '#E9D5FF']   # Purple
            ],
            'accent': '#8B5CF6',
            'secondary': '#A78BFA',
            'icon': '⚡',
            'theme': 'TECH INNOVATION',
            'subtitle': f'Digital • Future • {get_trend_indicator(popularity, source)}'
        },
        'lifestyle': {
            'gradients': [
                ['#064E3B', '#047857', '#059669', '#10B981', '#34D399'],  # Emerald
                ['#14B8A6', '#2DD4BF', '#5EEAD4', '#99F6E4', '#CCFBF1']   # Teal
            ],
            'accent': '#10B981',
            'secondary': '#34D399',
            'icon': '🌟',
            'theme': 'LIFESTYLE PREMIUM',
            'subtitle': f'Authentic • Wellness • {get_trend_indicator(popularity, source)}'
        },
        'food': {
            'gradients': [
                ['#92400E', '#B45309', '#D97706', '#F59E0B', '#FBBF24'],  # Amber
                ['#F97316', '#FB923C', '#FDBA74', '#FED7AA', '#FEF3C7']   # Orange
            ],
            'accent': '#F59E0B',
            'secondary': '#FCD34D',
            'icon': '🍽️',
            'theme': 'CULINARY ART',
            'subtitle': f'Gourmet • Fresh • {get_trend_indicator(popularity, source)}'
        },
        'nature': {
            'gradients': [
                ['#14532D', '#166534', '#15803D', '#16A34A', '#22C55E'],  # Green
                ['#4ADE80', '#86EFAC', '#BBF7D0', '#DCFCE7', '#F0FDF4']   # Light Green
            ],
            'accent': '#22C55E',
            'secondary': '#4ADE80',
            'icon': '🌿',
            'theme': 'NATURAL BEAUTY',
            'subtitle': f'Environmental • Scenic • {get_trend_indicator(popularity, source)}'
        },
        'general': {
            'gradients': [
                ['#1F2937', '#374151', '#4B5563', '#6B7280', '#9CA3AF'],  # Gray
                ['#D1D5DB', '#E5E7EB', '#F3F4F6', '#F9FAFB', '#FFFFFF']   # Light Gray
            ],
            'accent': '#6B7280',
            'secondary': '#9CA3AF',
            'icon': '📸',
            'theme': 'PREMIUM STOCK',
            'subtitle': f'Professional • Quality • {get_trend_indicator(popularity, source)}'
        }
    }
    
    design = category_designs.get(category, category_designs['general'])
    
    # Create high-resolution canvas
    width, height = Config.IMAGE_SIZE
    img = Image.new('RGB', (width, height), '#000000')
    draw = ImageDraw.Draw(img)
    
    # Choose gradient based on popularity and number
    gradient_index = 0 if popularity > 80 else 1
    if gradient_index >= len(design['gradients']):
        gradient_index = 0
    gradient_colors = design['gradients'][gradient_index]
    
    # Create sophisticated gradient with curves
    for y in range(height):
        position = y / height
        
        # Apply different curves based on source
        if source in ['seasonal', 'tech_trends']:
            # S-curve for trending content
            curved_position = 0.5 * (1 + math.sin(math.pi * (position - 0.5)))
        elif source in ['google_suggestions', 'business_trends']:
            # Ease-in-out for professional content
            curved_position = position * position * (3.0 - 2.0 * position)
        else:
            # Linear for standard content
            curved_position = position
        
        # Multi-segment gradient
        segment_count = len(gradient_colors) - 1
        segment_size = 1.0 / segment_count
        segment_index = min(int(curved_position / segment_size), segment_count - 1)
        segment_position = (curved_position - segment_index * segment_size) / segment_size
        
        # Smooth color interpolation
        color1 = gradient_colors[segment_index]
        color2 = gradient_colors[segment_index + 1]
        
        r1, g1, b1 = tuple(int(color1[i:i+2], 16) for i in (1, 3, 5))
        r2, g2, b2 = tuple(int(color2[i:i+2], 16) for i in (1, 3, 5))
        
        r = int(r1 + (r2 - r1) * segment_position)
        g = int(g1 + (g2 - g1) * segment_position)
        b = int(b1 + (b2 - b1) * segment_position)
        
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Load scalable fonts
    fonts = load_professional_fonts(width)
    
    # Add subtle texture based on popularity
    add_market_texture(draw, width, height, design['accent'], popularity)
    
    # Professional border system
    create_enhanced_borders(draw, width, height, design['accent'], design['secondary'], popularity)
    
    # Content layout with market data
    create_market_aware_layout(draw, width, height, keyword, design, fonts, number, popularity, source)
    
    # Save with maximum quality
    img.save(filepath, 'JPEG', quality=Config.IMAGE_QUALITY, optimize=True, progressive=True)

def get_trend_indicator(popularity: int, source: str) -> str:
    """Get trend indicator based on popularity and source"""
    if popularity >= 90:
        return "🔥 VIRAL"
    elif popularity >= 85:
        return "📈 TRENDING"
    elif popularity >= 75:
        return "⭐ POPULAR"
    elif source in ['seasonal', 'tech_trends', 'business_trends']:
        return "🚀 RISING"
    else:
        return "💎 QUALITY"

def load_professional_fonts(canvas_width: int):
    """Load professional fonts with better scaling"""
    scale = canvas_width / 1600
    
    font_sizes = {
        'icon': int(100 * scale),
        'title': int(56 * scale),
        'keyword': int(48 * scale),
        'subtitle': int(24 * scale),
        'body': int(20 * scale),
        'small': int(16 * scale),
        'tiny': int(14 * scale)
    }
    
    # Professional font paths
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SF-Pro.ttf",
        "/System/Library/Fonts/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf"
    ]
    
    fonts = {}
    
    for font_type, size in font_sizes.items():
        font_loaded = False
        
        for font_path in font_paths:
            try:
                fonts[font_type] = ImageFont.truetype(font_path, size)
                font_loaded = True
                break
            except (OSError, IOError):
                continue
        
        if not font_loaded:
            try:
                fonts[font_type] = ImageFont.load_default()
            except:
                fonts[font_type] = None
    
    return fonts

def add_market_texture(draw, width: int, height: int, accent_color: str, popularity: int):
    """Add market-aware texture based on popularity"""
    r, g, b = tuple(int(accent_color[i:i+2], 16) for i in (1, 3, 5))
    
    # Texture density based on popularity
    base_density = 0.0003
    popularity_multiplier = popularity / 100
    texture_density = int(width * height * base_density * popularity_multiplier)
    
    for _ in range(texture_density):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        
        # Vary intensity based on market position
        if popularity > 85:
            intensity_range = (20, 40)  # More vibrant for trending
        else:
            intensity_range = (10, 25)  # Subtle for standard
        
        intensity = random.randint(*intensity_range)
        alpha = random.choice([0.1, 0.15, 0.2, 0.25])
        
        tr = max(0, min(255, int(r * (1 + alpha))))
        tg = max(0, min(255, int(g * (1 + alpha))))
        tb = max(0, min(255, int(b * (1 + alpha))))
        
        size = random.choice([1, 1, 1, 2, 2, 3])  # Varied sizes
        
        if size == 1:
            draw.point((x, y), fill=(tr, tg, tb))
        else:
            draw.ellipse([x, y, x + size, y + size], fill=(tr, tg, tb))

def create_enhanced_borders(draw, width: int, height: int, accent: str, secondary: str, popularity: int):
    """Create enhanced borders based on market performance"""
    accent_rgb = tuple(int(accent[i:i+2], 16) for i in (1, 3, 5))
    secondary_rgb = tuple(int(secondary[i:i+2], 16) for i in (1, 3, 5))
    
    # Border thickness based on popularity
    if popularity >= 90:
        margins = [20, 25, 30, 35]  # Thicker for high-demand
        widths = [4, 3, 2, 1]
    elif popularity >= 75:
        margins = [25, 30, 35]
        widths = [3, 2, 1]
    else:
        margins = [30, 35]
        widths = [2, 1]
    
    colors = [accent_rgb, secondary_rgb, (255, 255, 255), (240, 240, 240)]
    
    for i, (margin, width_val) in enumerate(zip(margins, widths)):
        color = colors[min(i, len(colors) - 1)]
        
        # Ensure valid coordinates
        x1, y1 = margin, margin
        x2, y2 = width - margin, height - margin
        
        if x2 > x1 and y2 > y1:
            draw.rectangle([x1, y1, x2, y2], outline=color, width=width_val)

def create_market_aware_layout(draw, width: int, height: int, keyword: str, design: dict, fonts: dict, number: int, popularity: int, source: str):
    """Create layout with market awareness"""
    
    center_x = width // 2
    center_y = height // 2
    
    # Colors
    accent_rgb = tuple(int(design['accent'][i:i+2], 16) for i in (1, 3, 5))
    secondary_rgb = tuple(int(design['secondary'][i:i+2], 16) for i in (1, 3, 5))
    
    # 1. Icon with glow
    icon_y = center_y - 200
    if fonts['icon']:
        create_glowing_text(draw, center_x, icon_y, design['icon'], fonts['icon'], 'white', design['accent'])
    
    # 2. Theme title
    theme_y = center_y - 120
    if fonts['title']:
        create_centered_text(draw, center_x, theme_y, design['theme'], fonts['title'], 'white')
    
    # 3. Keyword with enhanced styling
    keyword_y = center_y + 10
    keyword_text = keyword.upper()
    if fonts['keyword']:
        create_premium_keyword_box(draw, center_x, keyword_y, keyword_text, fonts['keyword'], accent_rgb, secondary_rgb, popularity)
    
    # 4. Subtitle with market info
    subtitle_y = center_y + 90
    if fonts['subtitle']:
        create_centered_text(draw, center_x, subtitle_y, design['subtitle'], fonts['subtitle'], secondary_rgb)
    
    # 5. Market indicators
    indicators_y = center_y + 130
    market_text = f"Market Score: {popularity}% • Source: {source.replace('_', ' ').title()}"
    if fonts['small']:
        create_centered_text(draw, center_x, indicators_y, market_text, fonts['small'], (180, 180, 180))
    
    # 6. Professional footer with enhanced info
    create_enhanced_footer(draw, width, height, fonts['tiny'], secondary_rgb, number, popularity)

def create_glowing_text(draw, x: int, y: int, text: str, font, color, glow_color: str):
    """Create text with professional glow effect"""
    if not font:
        return
    
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except:
        text_width = len(text) * (font.size // 2)
        text_height = font.size
    
    text_x = x - text_width // 2
    text_y = y - text_height // 2
    
    # Enhanced glow
    glow_rgb = tuple(int(glow_color[i:i+2], 16) for i in (1, 3, 5))
    
    # Multiple glow layers for depth
    for offset in range(5, 0, -1):
        alpha = 30 + (5 - offset) * 15
        glow_alpha = tuple(min(255, c + alpha) for c in glow_rgb)
        
        for dx in range(-offset, offset + 1):
            for dy in range(-offset, offset + 1):
                if dx == 0 and dy == 0:
                    continue
                distance = math.sqrt(dx*dx + dy*dy)
                if distance <= offset:
                    intensity = 1 - (distance / offset)
                    final_alpha = tuple(int(c * intensity) for c in glow_alpha)
                    draw.text((text_x + dx, text_y + dy), text, fill=final_alpha, font=font)
    
    # Main text
    draw.text((text_x, text_y), text, fill=color, font=font)

def create_centered_text(draw, x: int, y: int, text: str, font, color):
    """Create professionally centered text"""
    if not font:
        return
    
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except:
        text_width = len(text) * (font.size // 3)
        text_height = font.size
    
    text_x = x - text_width // 2
    text_y = y - text_height // 2
    
    draw.text((text_x, text_y), text, fill=color, font=font)

def create_premium_keyword_box(draw, x: int, y: int, text: str, font, bg_color: tuple, border_color: tuple, popularity: int):
    """Create premium keyword box with market styling"""
    if not font:
        return
    
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except:
        text_width = len(text) * (font.size // 2)
        text_height = font.size
    
    # Box dimensions based on popularity
    base_padding = font.size // 2
    popularity_bonus = int(base_padding * (popularity / 100) * 0.3)
    padding_x = base_padding + popularity_bonus
    padding_y = base_padding // 2 + popularity_bonus // 2
    
    box_x1 = x - text_width // 2 - padding_x
    box_y1 = y - text_height // 2 - padding_y
    box_x2 = x + text_width // 2 + padding_x
    box_y2 = y + text_height // 2 + padding_y
    
    # Ensure valid coordinates
    if box_x2 <= box_x1 or box_y2 <= box_y1:
        return
    
    # Enhanced gradient background
    box_height = box_y2 - box_y1
    for i in range(box_height):
        ratio = i / box_height
        
        # Market-aware gradient curve
        if popularity > 85:
            # Vibrant curve for trending
            curved_ratio = 0.5 * (1 + math.sin(math.pi * ratio))
        else:
            # Professional curve for standard
            curved_ratio = ratio * ratio * (3.0 - 2.0 * ratio)
        
        r = int(bg_color[0] + (border_color[0] - bg_color[0]) * curved_ratio * 0.4)
        g = int(bg_color[1] + (border_color[1] - bg_color[1]) * curved_ratio * 0.4)
        b = int(bg_color[2] + (border_color[2] - bg_color[2]) * curved_ratio * 0.4)
        
        draw.line([(box_x1, box_y1 + i), (box_x2, box_y1 + i)], fill=(r, g, b))
    
    # Enhanced border based on popularity
    border_width = 3 if popularity > 85 else 2
    draw.rectangle([box_x1, box_y1, box_x2, box_y2], outline=border_color, width=border_width)
    
    # Premium corner accents for high-demand content
    if popularity > 80:
        corner_size = 8
        # Top corners
        draw.rectangle([box_x1, box_y1, box_x1 + corner_size, box_y1 + 2], fill=(255, 255, 255))
        draw.rectangle([box_x2 - corner_size, box_y1, box_x2, box_y1 + 2], fill=(255, 255, 255))
        # Bottom corners
        draw.rectangle([box_x1, box_y2 - 2, box_x1 + corner_size, box_y2], fill=(255, 255, 255))
        draw.rectangle([box_x2 - corner_size, box_y2 - 2, box_x2, box_y2], fill=(255, 255, 255))
    
    # Text
    text_x = x - text_width // 2
    text_y = y - text_height // 2
    draw.text((text_x, text_y), text, fill='white', font=font)

def create_enhanced_footer(draw, width: int, height: int, font, color: tuple, number: int, popularity: int):
    """Create enhanced footer with market data"""
    if not font:
        return
    
    footer_y = height - 35
    
    # Left: Enhanced generation info
    left_text = f"Generated {datetime.now().strftime('%B %Y')} • #{number:02d} • Score: {popularity}%"
    draw.text((40, footer_y), left_text, fill=color, font=font)
    
    # Right: Enhanced specs
    right_text = f"{Config.IMAGE_SIZE[0]}×{Config.IMAGE_SIZE[1]} • AI Enhanced • Commercial Ready"
    try:
        bbox = draw.textbbox((0, 0), right_text, font=font)
        right_width = bbox[2] - bbox[0]
    except:
        right_width = len(right_text) * (font.size // 2)
    
    draw.text((width - right_width - 40, footer_y), right_text, fill=color, font=font)

def create_prompt(keyword: str, category: str, popularity: int = 75) -> str:
    """Create market-aware prompt for Gemini Imagen"""
    
    # Base style templates
    style_templates = {
        'business': "professional corporate stock photography, modern office environment, business meeting, clean composition",
        'technology': "cutting-edge technology stock photo, futuristic interface, clean minimalist aesthetic, innovation", 
        'lifestyle': "authentic lifestyle stock photography, natural lighting, contemporary setting, wellness focus",
        'food': "professional food stock photography, appetizing presentation, natural lighting, gourmet styling",
        'nature': "natural landscape stock photography, environmental beauty, golden hour lighting, scenic view",
        'general': "premium commercial stock photography, professional composition, studio lighting, clean background"
    }
    
    base_style = style_templates.get(category, style_templates['general'])
    
    # Enhanced prompt based on popularity
    if popularity >= 90:
        quality_tier = "Ultra-premium viral-quality"
        enhancement = "trending composition, market-leading appeal, viral potential"
    elif popularity >= 80:
        quality_tier = "Premium high-demand"
        enhancement = "trending style, commercial appeal, market-ready"
    elif popularity >= 70:
        quality_tier = "Professional quality"
        enhancement = "contemporary style, commercial viability"
    else:
        quality_tier = "High-quality"
        enhancement = "professional standard, clean execution"
    
    # Comprehensive prompt
    prompt = f"""{quality_tier} commercial stock photograph: {keyword}. {base_style}. {enhancement}. Professional photography equipment, perfect studio lighting, razor-sharp focus, commercial licensing ready. Ultra-clean composition without any text overlays or watermarks, optimized for marketing and advertising applications. Maximum resolution, gallery-grade professional output."""
    
    return prompt.strip()

def test_gemini_connection():
    """Test Gemini API connection with enhanced debugging"""
    if not GEMINI_AVAILABLE:
        print("❌ Gemini client not available")
        return False
    
    try:
        print("🧪 Testing Gemini Imagen API connection...")
        
        response = client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt='A simple blue circle on white background, clean minimalist design',
            config=types.GenerateImagesConfig(number_of_images=1)
        )
        
        if response.generated_images:
            print("✅ Gemini API connection successful!")
            
            # Test image extraction
            generated_image = response.generated_images[0]
            genai_image = generated_image.image
            
            print(f"🔍 Response structure validated:")
            print(f"   GeneratedImage type: {type(generated_image)}")
            print(f"   Image type: {type(genai_image)}")
            print(f"   Available attributes: {[attr for attr in dir(genai_image) if not attr.startswith('_')][:10]}")
            
            return True
        else:
            print("❌ No images in API response")
            return False
            
    except Exception as e:
        error_msg = str(e).lower()
        if "billed users" in error_msg:
            print("💳 Gemini requires billing - enable in Google Cloud Console")
        elif "unauthenticated" in error_msg:
            print("🔐 Authentication failed - check API key configuration")
        elif "permission denied" in error_msg:
            print("🔒 Permission denied - enable Imagen API in Google Cloud")
        elif "quota" in error_msg:
            print("📊 API quota exceeded - check usage limits")
        else:
            print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    # Enhanced testing with real scraper data simulation
    print("🧪 Testing enhanced image generation system...")
    
    # Test API connection
    api_works = test_gemini_connection()
    
    # Test with realistic scraper data
    test_keywords = [
        {
            'keyword': 'remote work productivity',
            'category': 'business',
            'popularity': 92,
            'source': 'google_suggestions'
        },
        {
            'keyword': 'artificial intelligence innovation',
            'category': 'technology',
            'popularity': 88,
            'source': 'tech_trends'
        },
        {
            'keyword': 'sustainable lifestyle choices',
            'category': 'lifestyle',
            'popularity': 85,
            'source': 'business_trends'
        }
    ]
    
    os.makedirs('test_output', exist_ok=True)
    results = generate_images(test_keywords, 'test_output')
    
    print(f"\n✅ Enhanced test completed!")
    print(f"📊 Generated {len(results)} images with market-aware styling")
    
    for result in results:
        popularity = result.get('popularity', 'N/A')
        source = result.get('source', 'unknown')
        method = result.get('generation_method', 'unknown')
        
        print(f"📸 {result['filename']}")
        print(f"   📊 {popularity}% popularity | {source} | {method}")
        print(f"   💾 {result['file_size']} bytes | {result['status']}")