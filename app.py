import os
import json
import schedule
import time
import logging
import traceback
from datetime import datetime, timedelta
import shutil
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('adobe_stock_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import modules with comprehensive error handling
try:
    from scraper import scrape_adobe_trends
    SCRAPER_AVAILABLE = True
    logger.info("✅ Scraper module loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Scraper module not found: {e}")
    SCRAPER_AVAILABLE = False

try:
    from generator import generate_images, test_gemini_connection
    GENERATOR_AVAILABLE = True
    logger.info("✅ Generator module loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Generator module not found: {e}")
    GENERATOR_AVAILABLE = False

try:
    from metadata import create_metadata
    METADATA_AVAILABLE = True
    logger.info("✅ Metadata module loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Metadata module not found: {e}")
    METADATA_AVAILABLE = False

try:
    from config import Config
    CONFIG_AVAILABLE = True
    logger.info("✅ Config module loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Config module not found: {e}")
    CONFIG_AVAILABLE = False
    # Fallback config
    class Config:
        DAILY_IMAGE_LIMIT = 10
        OUTPUT_BASE_DIR = 'output'
        CLEANUP_DAYS = 30
        LOG_LEVEL = 'INFO'

def daily_workflow() -> bool:
    """Enhanced daily automation workflow with comprehensive error handling"""
    start_time = time.time()
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = f"{Config.OUTPUT_BASE_DIR}/{today}"
    
    # Create comprehensive directory structure
    directories = [
        output_dir,
        f"{output_dir}/images",
        f"{output_dir}/metadata", 
        f"{output_dir}/upload_ready",
        f"{output_dir}/reports",
        f"{output_dir}/logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    logger.info(f"🚀 Starting daily workflow for {today}")
    logger.info(f"📁 Output directory: {output_dir}")
    
    workflow_report = {
        'date': today,
        'start_time': datetime.now().isoformat(),
        'steps_completed': [],
        'errors': [],
        'metrics': {},
        'files_created': [],
        'success': False
    }
    
    try:
        # Step 1: System Health Check
        logger.info("🔍 Running system health check...")
        health_check_result = run_health_check()
        workflow_report['health_check'] = health_check_result
        workflow_report['steps_completed'].append('health_check')
        
        if not health_check_result['overall_status']:
            raise Exception("System health check failed - see health_check details")
        
        # Step 2: Scrape trends from multiple sources
        logger.info("📊 Scraping trending data from multiple sources...")
        if SCRAPER_AVAILABLE:
            trends_data = scrape_adobe_trends()
            trends_file = f"{output_dir}/trends_data.json"
            
            with open(trends_file, "w", encoding='utf-8') as f:
                json.dump(trends_data, f, indent=2, ensure_ascii=False)
            
            workflow_report['files_created'].append(trends_file)
            workflow_report['metrics']['sources_scraped'] = len(trends_data.get('sources_used', []))
            workflow_report['metrics']['trends_found'] = len(trends_data.get('trending_searches', []))
            
            logger.info(f"✅ Scraped {workflow_report['metrics']['trends_found']} trends from {workflow_report['metrics']['sources_scraped']} sources")
        else:
            logger.warning("⚠️ Using fallback trend data")
            trends_data = get_fallback_trends_data()
        
        workflow_report['steps_completed'].append('scraping')
        
        # Step 3: Process and rank keywords
        logger.info("🔍 Processing and ranking keywords...")
        processed_keywords = process_keywords_enhanced(trends_data)
        
        keywords_file = f"{output_dir}/processed_keywords.json"
        with open(keywords_file, "w", encoding='utf-8') as f:
            json.dump(processed_keywords, f, indent=2, ensure_ascii=False)
        
        workflow_report['files_created'].append(keywords_file)
        workflow_report['metrics']['keywords_processed'] = len(processed_keywords)
        workflow_report['steps_completed'].append('keyword_processing')
        
        logger.info(f"✅ Processed {len(processed_keywords)} keywords")
        
        # Step 4: Generate images with AI or placeholders
        logger.info("🎨 Generating images...")
        if GENERATOR_AVAILABLE:
            selected_keywords = processed_keywords[:Config.DAILY_IMAGE_LIMIT]
            generated_images = generate_images(selected_keywords, output_dir)
            
            workflow_report['metrics']['images_requested'] = len(selected_keywords)
            workflow_report['metrics']['images_generated'] = len(generated_images)
            
            # Categorize generation methods
            ai_generated = sum(1 for img in generated_images if img.get('status') == 'ai_generated')
            placeholder_generated = len(generated_images) - ai_generated
            
            workflow_report['metrics']['ai_generated'] = ai_generated
            workflow_report['metrics']['placeholder_generated'] = placeholder_generated
            
            logger.info(f"✅ Generated {len(generated_images)} images ({ai_generated} AI, {placeholder_generated} placeholders)")
        else:
            logger.warning("⚠️ Generator not available, creating mock images")
            generated_images = create_mock_images(processed_keywords[:Config.DAILY_IMAGE_LIMIT], output_dir)
        
        workflow_report['steps_completed'].append('image_generation')
        
        # Step 5: Create comprehensive metadata
        logger.info("📝 Creating comprehensive metadata...")
        if METADATA_AVAILABLE and generated_images:
            create_metadata(generated_images, output_dir)
            workflow_report['metrics']['metadata_files'] = len(generated_images)
            logger.info(f"✅ Created metadata for {len(generated_images)} images")
        else:
            logger.warning("⚠️ Metadata creation skipped")
            create_basic_metadata(generated_images, output_dir)
        
        workflow_report['steps_completed'].append('metadata_creation')
        
        # Step 6: Prepare upload-ready files
        logger.info("📦 Preparing upload-ready files...")
        upload_ready_count = prepare_upload_ready_files(generated_images, output_dir)
        workflow_report['metrics']['upload_ready_files'] = upload_ready_count
        workflow_report['steps_completed'].append('upload_preparation')
        
        # Step 7: Generate workflow report
        logger.info("📊 Generating workflow report...")
        create_workflow_report(workflow_report, output_dir, generated_images)
        workflow_report['steps_completed'].append('report_generation')
        
        # Step 8: Cleanup old data
        logger.info("🗑️ Cleaning up old data...")
        if Config.AUTO_CLEANUP_ENABLED if hasattr(Config, 'AUTO_CLEANUP_ENABLED') else True:
            cleanup_count = cleanup_old_data(Config.CLEANUP_DAYS)
            workflow_report['metrics']['files_cleaned'] = cleanup_count
        workflow_report['steps_completed'].append('cleanup')
        
        # Calculate metrics
        end_time = time.time()
        workflow_report['end_time'] = datetime.now().isoformat()
        workflow_report['duration_minutes'] = round((end_time - start_time) / 60, 2)
        workflow_report['success'] = True
        
        logger.info(f"🎉 Daily workflow completed successfully in {workflow_report['duration_minutes']} minutes!")
        logger.info(f"📊 Summary: {len(generated_images)} images created, {upload_ready_count} upload-ready files")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Error in daily workflow: {error_msg}")
        logger.error(f"📚 Traceback: {traceback.format_exc()}")
        
        workflow_report['errors'].append({
            'error': error_msg,
            'timestamp': datetime.now().isoformat(),
            'traceback': traceback.format_exc()
        })
        workflow_report['success'] = False
        workflow_report['end_time'] = datetime.now().isoformat()
        
        # Save error report
        error_report_file = f"{output_dir}/error_report.json"
        try:
            with open(error_report_file, "w", encoding='utf-8') as f:
                json.dump(workflow_report, f, indent=2, ensure_ascii=False)
        except:
            pass
        
        return False

def run_health_check() -> Dict:
    """Comprehensive system health check"""
    health_status = {
        'timestamp': datetime.now().isoformat(),
        'modules': {},
        'api_status': {},
        'file_system': {},
        'configuration': {},
        'overall_status': True
    }
    
    # Check modules
    health_status['modules']['scraper'] = SCRAPER_AVAILABLE
    health_status['modules']['generator'] = GENERATOR_AVAILABLE
    health_status['modules']['metadata'] = METADATA_AVAILABLE
    health_status['modules']['config'] = CONFIG_AVAILABLE
    
    # Check API connections
    if GENERATOR_AVAILABLE:
        try:
            from generator import test_gemini_connection
            api_status = test_gemini_connection()
            health_status['api_status']['gemini'] = api_status
        except Exception as e:
            health_status['api_status']['gemini'] = False
            health_status['api_status']['gemini_error'] = str(e)
    
    # Check file system
    try:
        test_dir = f"{Config.OUTPUT_BASE_DIR}/health_check"
        os.makedirs(test_dir, exist_ok=True)
        test_file = f"{test_dir}/test.txt"
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        os.rmdir(test_dir)
        health_status['file_system']['write_access'] = True
    except Exception as e:
        health_status['file_system']['write_access'] = False
        health_status['file_system']['error'] = str(e)
        health_status['overall_status'] = False
    
    # Check configuration
    if CONFIG_AVAILABLE:
        try:
            config_issues = Config.validate_config()
            health_status['configuration']['valid'] = len(config_issues) == 0
            health_status['configuration']['issues'] = config_issues
            if config_issues:
                health_status['overall_status'] = False
        except Exception as e:
            health_status['configuration']['valid'] = False
            health_status['configuration']['error'] = str(e)
    
    return health_status

def process_keywords_enhanced(trends_data: Dict) -> List[Dict]:
    """Enhanced keyword processing with market intelligence"""
    keywords = []
    trending_searches = trends_data.get('trending_searches', [])
    
    if not trending_searches:
        logger.warning("⚠️ No trending searches found, using fallback keywords")
        keywords = get_fallback_keywords()
    else:
        current_month = datetime.now().month
        
        for item in trending_searches:
            keyword_data = {
                'keyword': item.get('keyword', 'unknown'),
                'popularity': item.get('popularity', 0),
                'category': item.get('category', 'general'),
                'source': item.get('source', 'unknown'),
                'original_data': item
            }
            
            # Apply seasonal boost if config available
            if CONFIG_AVAILABLE and hasattr(Config, 'get_seasonal_boost'):
                seasonal_boost = Config.get_seasonal_boost(keyword_data['category'], current_month)
                keyword_data['seasonal_popularity'] = round(keyword_data['popularity'] * seasonal_boost)
            else:
                keyword_data['seasonal_popularity'] = keyword_data['popularity']
            
            # Check if keyword is allowed
            if CONFIG_AVAILABLE and hasattr(Config, 'is_keyword_allowed'):
                if not Config.is_keyword_allowed(keyword_data['keyword']):
                    logger.warning(f"⚠️ Keyword '{keyword_data['keyword']}' is in forbidden list, skipping")
                    continue
            
            keywords.append(keyword_data)
    
    # Sort by seasonal popularity for better market timing
    sorted_keywords = sorted(keywords, key=lambda x: x.get('seasonal_popularity', x.get('popularity', 0)), reverse=True)
    
    logger.info(f"✅ Processed {len(sorted_keywords)} keywords with market intelligence")
    return sorted_keywords

def prepare_upload_ready_files(generated_images: List[Dict], output_dir: str) -> int:
    """Prepare files for upload to stock platforms"""
    upload_dir = f"{output_dir}/upload_ready"
    count = 0
    
    for image_info in generated_images:
        try:
            source_path = image_info['filepath']
            filename = image_info['filename']
            
            # Copy image to upload directory
            if os.path.exists(source_path):
                upload_path = f"{upload_dir}/{filename}"
                shutil.copy2(source_path, upload_path)
                count += 1
                
                # Create upload info file
                upload_info = {
                    'filename': filename,
                    'title': f"Professional {image_info['keyword'].title()} Stock Photo",
                    'description': f"High-quality stock photograph featuring {image_info['keyword']}. Perfect for commercial use.",
                    'keywords': [image_info['keyword'], image_info['category'], 'stock photo', 'commercial use'],
                    'category': image_info['category'],
                    'upload_ready': True,
                    'file_size': image_info.get('file_size', 0),
                    'dimensions': image_info.get('dimensions', 'unknown')
                }
                
                info_file = f"{upload_dir}/{filename}.info.json"
                with open(info_file, 'w', encoding='utf-8') as f:
                    json.dump(upload_info, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"❌ Error preparing {filename} for upload: {e}")
    
    logger.info(f"✅ Prepared {count} files for upload")
    return count

def create_workflow_report(workflow_report: Dict, output_dir: str, generated_images: List[Dict]):
    """Create comprehensive workflow report"""
    report_file = f"{output_dir}/reports/workflow_report.json"
    
    # Add detailed image analysis
    if generated_images:
        workflow_report['image_analysis'] = {
            'total_images': len(generated_images),
            'categories': {},
            'sources': {},
            'average_popularity': 0,
            'file_sizes': []
        }
        
        total_popularity = 0
        for img in generated_images:
            # Category analysis
            category = img.get('category', 'unknown')
            if category not in workflow_report['image_analysis']['categories']:
                workflow_report['image_analysis']['categories'][category] = 0
            workflow_report['image_analysis']['categories'][category] += 1
            
            # Source analysis
            source = img.get('source', 'unknown')
            if source not in workflow_report['image_analysis']['sources']:
                workflow_report['image_analysis']['sources'][source] = 0
            workflow_report['image_analysis']['sources'][source] += 1
            
            # Popularity tracking
            popularity = img.get('popularity', 0)
            total_popularity += popularity
            
            # File size tracking
            file_size = img.get('file_size', 0)
            workflow_report['image_analysis']['file_sizes'].append(file_size)
        
        workflow_report['image_analysis']['average_popularity'] = round(total_popularity / len(generated_images), 1)
    
    # Save comprehensive report
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(workflow_report, f, indent=2, ensure_ascii=False)
    
    # Create human-readable summary
    summary_file = f"{output_dir}/reports/summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"Adobe Stock Generation Report - {workflow_report['date']}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Workflow Status: {'✅ SUCCESS' if workflow_report['success'] else '❌ FAILED'}\n")
        f.write(f"Duration: {workflow_report.get('duration_minutes', 0)} minutes\n")
        f.write(f"Steps Completed: {len(workflow_report['steps_completed'])}\n\n")
        
        if 'metrics' in workflow_report:
            f.write("📊 Metrics:\n")
            for key, value in workflow_report['metrics'].items():
                f.write(f"   {key.replace('_', ' ').title()}: {value}\n")
        
        if 'errors' in workflow_report and workflow_report['errors']:
            f.write(f"\n❌ Errors ({len(workflow_report['errors'])}):\n")
            for error in workflow_report['errors']:
                f.write(f"   • {error['error']}\n")

def get_fallback_trends_data() -> Dict:
    """Fallback trending data when scraping fails"""
    return {
        'scrape_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'trending_searches': [
            {"keyword": "remote work", "popularity": 95, "category": "business", "source": "fallback"},
            {"keyword": "artificial intelligence", "popularity": 92, "category": "technology", "source": "fallback"},
            {"keyword": "sustainable living", "popularity": 88, "category": "lifestyle", "source": "fallback"},
            {"keyword": "digital transformation", "popularity": 85, "category": "business", "source": "fallback"},
            {"keyword": "healthy lifestyle", "popularity": 82, "category": "lifestyle", "source": "fallback"},
            {"keyword": "renewable energy", "popularity": 80, "category": "technology", "source": "fallback"},
            {"keyword": "mental health awareness", "popularity": 78, "category": "lifestyle", "source": "fallback"},
            {"keyword": "plant based nutrition", "popularity": 75, "category": "food", "source": "fallback"},
            {"keyword": "outdoor adventure", "popularity": 73, "category": "nature", "source": "fallback"},
            {"keyword": "minimalist design", "popularity": 70, "category": "lifestyle", "source": "fallback"}
        ],
        'sources_used': ['fallback'],
        'popular_categories': []
    }

def get_fallback_keywords() -> List[Dict]:
    """Fallback keywords when processing fails"""
    fallback_data = get_fallback_trends_data()
    return fallback_data['trending_searches']

def create_mock_images(keywords: List[Dict], output_dir: str) -> List[Dict]:
    """Create mock image data when generator is not available"""
    mock_images = []
    images_dir = f"{output_dir}/images"
    
    for i, keyword_data in enumerate(keywords):
        filename = f"mock_{i+1:02d}_{keyword_data['keyword'].replace(' ', '_')}.jpg"
        filepath = f"{images_dir}/{filename}"
        
        # Create empty file
        with open(filepath, 'w') as f:
            f.write("")
        
        mock_images.append({
            'filename': filename,
            'filepath': filepath,
            'keyword': keyword_data['keyword'],
            'category': keyword_data.get('category', 'general'),
            'popularity': keyword_data.get('popularity', 50),
            'source': keyword_data.get('source', 'mock'),
            'generated_at': datetime.now().isoformat(),
            'file_size': 0,
            'status': 'mock_image',
            'dimensions': '1600x1200'
        })
    
    return mock_images

def create_basic_metadata(generated_images: List[Dict], output_dir: str):
    """Create basic metadata when full metadata module is not available"""
    metadata_dir = f"{output_dir}/metadata"
    
    for image_info in generated_images:
        basic_metadata = {
            'filename': image_info['filename'],
            'keyword': image_info['keyword'],
            'category': image_info['category'],
            'created_at': image_info.get('generated_at', datetime.now().isoformat()),
            'basic_metadata_only': True
        }
        
        metadata_file = f"{metadata_dir}/{image_info['filename']}.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(basic_metadata, f, indent=2, ensure_ascii=False)

def cleanup_old_data(days_to_keep: int = 30) -> int:
    """Enhanced cleanup with better safety checks"""
    if days_to_keep <= 0:
        logger.warning("⚠️ Invalid cleanup days, skipping cleanup")
        return 0
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    output_base = Config.OUTPUT_BASE_DIR
    cleanup_count = 0
    
    if not os.path.exists(output_base):
        return 0
    
    for folder in os.listdir(output_base):
        folder_path = os.path.join(output_base, folder)
        
        if not os.path.isdir(folder_path):
            continue
        
        try:
            # Try to parse as date folder
            folder_date = datetime.strptime(folder, "%Y-%m-%d")
            
            if folder_date < cutoff_date:
                # Create backup if configured
                if hasattr(Config, 'BACKUP_BEFORE_CLEANUP') and Config.BACKUP_BEFORE_CLEANUP:
                    backup_dir = f"{Config.OUTPUT_BASE_DIR}/backups"
                    os.makedirs(backup_dir, exist_ok=True)
                    backup_path = f"{backup_dir}/{folder}_backup.tar.gz"
                    
                    # Create compressed backup
                    import tarfile
                    with tarfile.open(backup_path, "w:gz") as tar:
                        tar.add(folder_path, arcname=folder)
                    
                    logger.info(f"💾 Backed up {folder} to {backup_path}")
                
                # Remove original folder
                shutil.rmtree(folder_path)
                cleanup_count += 1
                logger.info(f"🗑️ Cleaned up {folder} (older than {days_to_keep} days)")
                
        except ValueError:
            # Skip non-date folders
            continue
        except Exception as e:
            logger.error(f"❌ Error cleaning up {folder}: {e}")
            continue
    
    if cleanup_count > 0:
        logger.info(f"✅ Cleanup completed: removed {cleanup_count} old folders")
    
    return cleanup_count

def run_scheduler():
    """Enhanced scheduler with better error handling and monitoring"""
    logger.info("🤖 Adobe Stock Automation Scheduler Started")
    logger.info("⏰ Scheduled to run daily at 08:00")
    
    # Schedule daily execution
    schedule.every().day.at("08:00").do(daily_workflow)
    
    # Optional: Add health check schedule
    schedule.every().hour.do(lambda: logger.info(f"🔄 Scheduler alive - {datetime.now().strftime('%H:%M:%S')}"))
    
    consecutive_failures = 0
    max_failures = 3
    
    try:
        while True:
            schedule.run_pending()
            
            # Monitor for consecutive failures
            if consecutive_failures >= max_failures:
                logger.error(f"❌ Too many consecutive failures ({consecutive_failures}), stopping scheduler")
                break
            
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("🛑 Scheduler stopped by user")
    except Exception as e:
        logger.error(f"❌ Scheduler error: {e}")
        consecutive_failures += 1

if __name__ == "__main__":
    print("=" * 60)
    print("🎯 Adobe Stock Automation System v2.0")
    print("=" * 60)
    
    # Display system status
    if CONFIG_AVAILABLE:
        print(f"📊 Configuration: ✅ Loaded")
        print(f"🎨 Daily limit: {Config.DAILY_IMAGE_LIMIT} images")
        print(f"📁 Output directory: {Config.OUTPUT_BASE_DIR}")
    else:
        print(f"📊 Configuration: ⚠️ Using defaults")
    
    print(f"🔧 Modules loaded:")
    print(f"   Scraper: {'✅' if SCRAPER_AVAILABLE else '❌'}")
    print(f"   Generator: {'✅' if GENERATOR_AVAILABLE else '❌'}")
    print(f"   Metadata: {'✅' if METADATA_AVAILABLE else '❌'}")
    
    # Menu options
    print("\n🎛️ Choose an option:")
    print("1. 🎬 Run workflow once now")
    print("2. 🤖 Start scheduler (runs daily at 08:00)")
    print("3. 🔍 Run system health check")
    print("4. 📊 View configuration summary")
    print("5. 👋 Exit")
    
    try:
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            print("\n🎬 Running workflow immediately...")
            success = daily_workflow()
            if success:
                print("\n🎉 Workflow completed successfully!")
            else:
                print("\n💥 Workflow failed! Check logs for details.")
                
        elif choice == "2":
            run_scheduler()
            
        elif choice == "3":
            print("\n🔍 Running system health check...")
            health_status = run_health_check()
            
            print(f"\n📊 Health Check Results:")
            print(f"Overall Status: {'✅ HEALTHY' if health_status['overall_status'] else '❌ ISSUES FOUND'}")
            
            for category, status in health_status.items():
                if category not in ['timestamp', 'overall_status']:
                    print(f"{category.title()}: {status}")
            
        elif choice == "4":
            if CONFIG_AVAILABLE:
                print(f"\n📊 Configuration Summary:")
                summary = Config.get_config_summary()
                for section, data in summary.items():
                    print(f"\n{section.title()}:")
                    for key, value in data.items():
                        print(f"   {key}: {value}")
            else:
                print("\n⚠️ Configuration module not available")
            
        elif choice == "5":
            print("👋 Goodbye!")
            
        else:
            print("❌ Invalid choice. Please run again and select 1-5.")
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stopped by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        logger.error(f"📚 Traceback: {traceback.format_exc()}")
        print(f"\n❌ Unexpected error occurred. Check logs for details.")