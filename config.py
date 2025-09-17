import os
from dotenv import load_dotenv
from typing import Dict, List, Tuple

# Load environment variables
load_dotenv()

class Config:
    """Comprehensive configuration for Adobe Stock generation system"""
    
    # ================================
    # API CONFIGURATION
    # ================================
    
    # Gemini API (Primary AI generation)
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = 'imagen-4.0-generate-001'
    GEMINI_MAX_RETRIES = 10
    GEMINI_TIMEOUT = 30
    
    # ================================
    # IMAGE GENERATION SETTINGS
    # ================================
    
    # Production settings for Adobe Stock
    DAILY_IMAGE_LIMIT = 10
    IMAGE_QUALITY = 98 # JPEG quality (85-100 recommended)
    IMAGE_SIZE = (4000, 6000)  # Adobe Stock recommended portrait
    IMAGE_SIZE_LANDSCAPE = (6000, 4000)  # Adobe Stock recommended landscape
    IMAGE_FORMAT = 'JPEG'
    
    # Alternative sizes for different markets
    IMAGE_SIZES = {
        'adobe_stock_portrait': (4000, 6000),
        'adobe_stock_landscape': (6000, 4000),
        'adobe_stock_square': (4000, 4000),
        'shutterstock_large': (5000, 3333),
        'getty_large': (5616, 3744),
        'web_optimized': (1920, 1280),
        'social_media': (1080, 1080)
    }
    
    # AI Generation settings
    AI_GENERATION_ENABLED = True
    FALLBACK_TO_PLACEHOLDER = True
    PLACEHOLDER_STYLE_PREMIUM = True
    
    # Rate limiting for AI APIs
    API_RATE_LIMIT_DELAY = 2  # seconds between calls
    API_BURST_LIMIT = 5  # max calls per minute
    
    # ================================
    # WEB SCRAPING CONFIGURATION
    # ================================
    
    # Request settings
    REQUEST_DELAY_MIN = 2
    REQUEST_DELAY_MAX = 5
    REQUEST_TIMEOUT = 15
    MAX_RETRIES = 3
    
    # User agents for rotation
    USER_AGENTS = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
    ]
    
    # Target websites
    SCRAPING_SOURCES = {
        'shutterstock': {
            'enabled': True,
            'url': 'https://www.shutterstock.com/explore/trending',
            'priority': 1,
            'max_keywords': 10
        },
        'unsplash': {
            'enabled': True,
            'url': 'https://unsplash.com/explore',
            'priority': 2,
            'max_keywords': 8
        },
        'pexels': {
            'enabled': True,
            'url': 'https://www.pexels.com/popular-searches/',
            'priority': 3,
            'max_keywords': 8
        },
        'google_trends': {
            'enabled': True,
            'priority': 4,
            'max_keywords': 10
        }
    }
    
    # ================================
    # METADATA CONFIGURATION
    # ================================
    
    # Creator information
    CREATOR_NAME = os.getenv('CREATOR_NAME', 'Professional AI Photography Studio')
    COMPANY_NAME = os.getenv('COMPANY_NAME', 'AI Stock Photography')
    CREATOR_EMAIL = os.getenv('CREATOR_EMAIL', 'info@aistockphoto.com')
    CREATOR_WEBSITE = os.getenv('CREATOR_WEBSITE', 'https://aistockphoto.com')
    
    # Copyright and licensing
    COPYRIGHT_TEMPLATE = "© {year} {company} - All Rights Reserved"
    LICENSE_TYPE = 'Standard License'
    USAGE_RIGHTS = 'Royalty Free - Commercial Use'
    
    # Adobe Stock specific metadata
    ADOBE_STOCK_METADATA = {
        'content_type': 'Photo',
        'model_release': False,
        'property_release': False,
        'adult_content': False,
        'editorial_use': False,
        'ai_generated': True,
        'software_used': 'Google Imagen 4.0'
    }
    
    # SEO optimization
    MAX_KEYWORDS_PER_IMAGE = 50
    MAX_TITLE_LENGTH = 200
    MAX_DESCRIPTION_LENGTH = 2000
    
    # ================================
    # FILE SYSTEM CONFIGURATION
    # ================================
    
    # Directory structure
    OUTPUT_BASE_DIR = 'output'
    BACKUP_DIR = 'backups'
    TEMP_DIR = 'temp'
    
    # Subdirectories
    SUBDIRS = {
        'images': 'images',
        'metadata': 'metadata',
        'upload_ready': 'upload_ready',
        'reports': 'reports',
        'logs': 'logs'
    }
    
    # File naming
    FILENAME_TEMPLATE = "stock_{number:02d}_{keyword}_{date}"
    DATE_FORMAT = "%Y%m%d"
    SAFE_FILENAME_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789_-"
    MAX_FILENAME_LENGTH = 100
    
    # Cleanup settings
    CLEANUP_DAYS = 30  # Keep data for 30 days
    AUTO_CLEANUP_ENABLED = True
    BACKUP_BEFORE_CLEANUP = True
    
    # ================================
    # MARKET INTELLIGENCE
    # ================================
    
    # Category definitions with market data
    CATEGORIES = {
        'business': {
            'name': 'Business',
            'subcategories': ['Corporate', 'Office', 'Meeting', 'Finance', 'Marketing'],
            'trending_keywords': ['remote work', 'digital transformation', 'team collaboration'],
            'market_demand': 'high',
            'seasonal_boost': {'january': 1.2, 'september': 1.1}
        },
        'technology': {
            'name': 'Technology',
            'subcategories': ['AI', 'Software', 'Hardware', 'Innovation', 'Digital'],
            'trending_keywords': ['artificial intelligence', 'machine learning', 'automation'],
            'market_demand': 'very_high',
            'seasonal_boost': {'january': 1.3, 'october': 1.1}
        },
        'lifestyle': {
            'name': 'Lifestyle',
            'subcategories': ['Health', 'Wellness', 'Family', 'Leisure', 'Home'],
            'trending_keywords': ['sustainable living', 'mental health', 'work life balance'],
            'market_demand': 'high',
            'seasonal_boost': {'january': 1.4, 'june': 1.2}
        },
        'food': {
            'name': 'Food & Beverage',
            'subcategories': ['Cooking', 'Healthy', 'Restaurant', 'Organic', 'Gourmet'],
            'trending_keywords': ['plant based', 'organic food', 'meal prep'],
            'market_demand': 'medium_high',
            'seasonal_boost': {'november': 1.3, 'december': 1.2}
        },
        'nature': {
            'name': 'Nature & Environment',
            'subcategories': ['Landscape', 'Wildlife', 'Conservation', 'Outdoor', 'Eco'],
            'trending_keywords': ['climate change', 'renewable energy', 'sustainability'],
            'market_demand': 'medium_high',
            'seasonal_boost': {'april': 1.3, 'october': 1.2}
        }
    }
    
    # Popularity thresholds
    POPULARITY_THRESHOLDS = {
        'viral': 95,
        'very_high': 90,
        'high': 80,
        'medium_high': 70,
        'medium': 60,
        'low': 50
    }
    
    # ================================
    # QUALITY CONTROL
    # ================================
    
    # AI prompt optimization
    PROMPT_TEMPLATES = {
        'premium': "Ultra-premium viral-quality commercial stock photograph",
        'standard': "Professional high-quality commercial stock photograph",
        'basic': "Quality commercial stock photograph"
    }
    
    # Image validation
    MIN_IMAGE_SIZE = (1000, 1000)
    MAX_FILE_SIZE_MB = 100
    REQUIRED_FORMATS = ['JPEG', 'PNG']
    
    # Content filters
    FORBIDDEN_KEYWORDS = [
        'nude', 'naked', 'sex', 'porn', 'violence', 'blood', 'weapon',
        'drug', 'alcohol', 'cigarette', 'politics', 'religion'
    ]
    
    # ================================
    # REPORTING & ANALYTICS
    # ================================
    
    # Performance tracking
    TRACK_GENERATION_TIME = True
    TRACK_API_USAGE = True
    TRACK_SUCCESS_RATE = True
    
    # Report generation
    DAILY_REPORT_ENABLED = True
    WEEKLY_REPORT_ENABLED = True
    REPORT_EMAIL_ENABLED = False
    REPORT_EMAIL = os.getenv('REPORT_EMAIL')
    
    # Analytics endpoints
    ANALYTICS_ENABLED = False
    ANALYTICS_ENDPOINT = os.getenv('ANALYTICS_ENDPOINT')
    
    # ================================
    # DEVELOPMENT & DEBUGGING
    # ================================
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Debug settings
    DEBUG_MODE = os.getenv('DEBUG', 'False').lower() == 'true'
    VERBOSE_LOGGING = DEBUG_MODE
    SAVE_DEBUG_IMAGES = DEBUG_MODE
    
    # Testing
    TEST_MODE = os.getenv('TEST_MODE', 'False').lower() == 'true'
    TEST_IMAGE_LIMIT = 3
    TEST_OUTPUT_DIR = 'test_output'
    
    # ================================
    # INTEGRATION SETTINGS
    # ================================
    
    # Webhook notifications
    WEBHOOK_ENABLED = False
    WEBHOOK_URL = os.getenv('WEBHOOK_URL')
    WEBHOOK_EVENTS = ['generation_complete', 'daily_summary']
    
    # External storage
    CLOUD_STORAGE_ENABLED = False
    CLOUD_STORAGE_PROVIDER = os.getenv('CLOUD_STORAGE_PROVIDER')  # 'aws', 'gcp', 'azure'
    CLOUD_STORAGE_BUCKET = os.getenv('CLOUD_STORAGE_BUCKET')
    
    # Database (for future use)
    DATABASE_ENABLED = False
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # ================================
    # HELPER METHODS
    # ================================
    
    @classmethod
    def get_image_size_for_category(cls, category: str) -> Tuple[int, int]:
        """Get optimal image size based on category"""
        if category in ['business', 'technology']:
            return cls.IMAGE_SIZE_LANDSCAPE  # Landscape for presentations
        else:
            return cls.IMAGE_SIZE  # Portrait for general use
    
    @classmethod
    def get_popularity_tier(cls, popularity: int) -> str:
        """Get popularity tier from score"""
        for tier, threshold in cls.POPULARITY_THRESHOLDS.items():
            if popularity >= threshold:
                return tier
        return 'low'
    
    @classmethod
    def is_keyword_allowed(cls, keyword: str) -> bool:
        """Check if keyword is allowed (not in forbidden list)"""
        keyword_lower = keyword.lower()
        return not any(forbidden in keyword_lower for forbidden in cls.FORBIDDEN_KEYWORDS)
    
    @classmethod
    def get_seasonal_boost(cls, category: str, month: int) -> float:
        """Get seasonal boost multiplier for category and month"""
        month_names = ['january', 'february', 'march', 'april', 'may', 'june',
                      'july', 'august', 'september', 'october', 'november', 'december']
        
        if month < 1 or month > 12:
            return 1.0
        
        month_name = month_names[month - 1]
        category_data = cls.CATEGORIES.get(category, {})
        seasonal_boosts = category_data.get('seasonal_boost', {})
        
        return seasonal_boosts.get(month_name, 1.0)
    
    @classmethod
    def get_prompt_template(cls, popularity: int) -> str:
        """Get appropriate prompt template based on popularity"""
        if popularity >= 90:
            return cls.PROMPT_TEMPLATES['premium']
        elif popularity >= 70:
            return cls.PROMPT_TEMPLATES['standard']
        else:
            return cls.PROMPT_TEMPLATES['basic']
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Required API keys
        if not cls.GEMINI_API_KEY:
            issues.append("GEMINI_API_KEY not set in environment variables")
        
        # Directory permissions
        try:
            os.makedirs(cls.OUTPUT_BASE_DIR, exist_ok=True)
        except PermissionError:
            issues.append(f"Cannot create output directory: {cls.OUTPUT_BASE_DIR}")
        
        # Image size validation
        if cls.IMAGE_SIZE[0] < cls.MIN_IMAGE_SIZE[0] or cls.IMAGE_SIZE[1] < cls.MIN_IMAGE_SIZE[1]:
            issues.append(f"IMAGE_SIZE {cls.IMAGE_SIZE} is below minimum {cls.MIN_IMAGE_SIZE}")
        
        # Quality validation
        if not (1 <= cls.IMAGE_QUALITY <= 100):
            issues.append(f"IMAGE_QUALITY {cls.IMAGE_QUALITY} must be between 1-100")
        
        return issues
    
    @classmethod
    def get_config_summary(cls) -> Dict:
        """Get summary of current configuration"""
        return {
            'generation': {
                'daily_limit': cls.DAILY_IMAGE_LIMIT,
                'image_size': cls.IMAGE_SIZE,
                'quality': cls.IMAGE_QUALITY,
                'ai_enabled': cls.AI_GENERATION_ENABLED
            },
            'scraping': {
                'sources_enabled': sum(1 for source in cls.SCRAPING_SOURCES.values() if source['enabled']),
                'request_delay': f"{cls.REQUEST_DELAY_MIN}-{cls.REQUEST_DELAY_MAX}s",
                'timeout': f"{cls.REQUEST_TIMEOUT}s"
            },
            'metadata': {
                'creator': cls.CREATOR_NAME,
                'max_keywords': cls.MAX_KEYWORDS_PER_IMAGE,
                'license': cls.LICENSE_TYPE
            },
            'files': {
                'output_dir': cls.OUTPUT_BASE_DIR,
                'cleanup_days': cls.CLEANUP_DAYS,
                'backup_enabled': cls.BACKUP_BEFORE_CLEANUP
            }
        }

# Environment-specific configurations
class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG_MODE = True
    VERBOSE_LOGGING = True
    DAILY_IMAGE_LIMIT = 3
    TEST_MODE = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG_MODE = False
    VERBOSE_LOGGING = False
    LOG_LEVEL = 'INFO'
    AUTO_CLEANUP_ENABLED = True
    DAILY_REPORT_ENABLED = True

class TestingConfig(Config):
    """Testing environment configuration"""
    DEBUG_MODE = True
    TEST_MODE = True
    DAILY_IMAGE_LIMIT = 2
    OUTPUT_BASE_DIR = 'test_output'
    CLEANUP_DAYS = 1

# Auto-select configuration based on environment
ENV = os.getenv('ENVIRONMENT', 'development').lower()

if ENV == 'production':
    Config = ProductionConfig
elif ENV == 'testing':
    Config = TestingConfig
else:
    Config = DevelopmentConfig

# Validate configuration on import
config_issues = Config.validate_config()
if config_issues:
    print("⚠️ Configuration Issues Found:")
    for issue in config_issues:
        print(f"   • {issue}")
    print("Please fix these issues before running the application.\n")

if __name__ == "__main__":
    # Configuration testing and display
    print("🔧 Adobe Stock Generation System Configuration")
    print("=" * 50)
    
    # Validation
    issues = Config.validate_config()
    if issues:
        print("❌ Configuration Issues:")
        for issue in issues:
            print(f"   • {issue}")
    else:
        print("✅ Configuration validated successfully")
    
    # Summary
    print(f"\n📊 Configuration Summary:")
    summary = Config.get_config_summary()
    for section, data in summary.items():
        print(f"\n{section.title()}:")
        for key, value in data.items():
            print(f"   {key}: {value}")
    
    # Environment info
    print(f"\n🌍 Environment: {ENV}")
    print(f"🔑 API Key configured: {'✅' if Config.GEMINI_API_KEY else '❌'}")
    print(f"📁 Output directory: {Config.OUTPUT_BASE_DIR}")
    print(f"🎨 Daily limit: {Config.DAILY_IMAGE_LIMIT} images")
    print(f"📏 Image size: {Config.IMAGE_SIZE[0]}x{Config.IMAGE_SIZE[1]}")