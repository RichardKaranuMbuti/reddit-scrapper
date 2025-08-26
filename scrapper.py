# scrapper.py
import pandas as pd
import time
import logging
import re
import csv
import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import schedule
from dotenv import load_dotenv
from pydantic import ValidationError

# Import our modules
from schemas import JobPosting, AnalyzedJobPosting, JobPostingAnalysis
from database import JobDatabase
from ai_service import AIAnalysisService
from config import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class RedditJobScraper:
    """Reddit job scraper for extracting developer/engineer job posts with OpenAI analysis"""
    
    def __init__(self, output_file: str = OUTPUT_FILE, log_level: str = LOG_LEVEL):
        self.output_file = output_file
        self.logger = logging.getLogger("RedditJobScraper")
        self.job_keywords = JOB_KEYWORDS
        self.setup_logging(log_level)
        self.driver = None
        
        # Initialize database
        self.db = JobDatabase()
        
        # OpenAI setup
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            self.logger.warning("OPENAI_API_KEY not found. Analysis will be skipped.")
            self.ai_service = None
        else:
            self.ai_service = AIAnalysisService(openai_api_key, OPENAI_MODEL)
        
    def setup_logging(self, log_level: str):
        """Setup logging configuration"""
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format,
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler()
            ]
        )
            
    def setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome WebDriver with optimized options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            # Method 1: Use webdriver-manager (recommended)
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                self.logger.info("Chrome WebDriver initialized with webdriver-manager")
                return driver
            except Exception as e:
                self.logger.warning(f"webdriver-manager failed: {e}")
                
            # Method 2: Try system ChromeDriver
            try:
                driver = webdriver.Chrome(options=chrome_options)
                self.logger.info("Chrome WebDriver initialized with system ChromeDriver")
                return driver
            except Exception as e:
                self.logger.warning(f"System ChromeDriver failed: {e}")
                
            # Method 3: Try Firefox as fallback
            try:
                from selenium.webdriver.firefox.options import Options as FirefoxOptions
                from webdriver_manager.firefox import GeckoDriverManager
                from selenium.webdriver.firefox.service import Service as FirefoxService
                
                self.logger.info("Trying Firefox as fallback...")
                firefox_options = FirefoxOptions()
                firefox_options.add_argument("--headless")
                
                firefox_service = FirefoxService(GeckoDriverManager().install())
                driver = webdriver.Firefox(service=firefox_service, options=firefox_options)
                self.logger.info("Firefox WebDriver initialized successfully")
                return driver
            except Exception as e:
                self.logger.warning(f"Firefox fallback failed: {e}")
                
            raise Exception("All WebDriver initialization methods failed")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            self.logger.info("Please ensure Chrome browser is installed, or try manual ChromeDriver setup")
            raise
            
    def contains_job_keywords(self, title: str) -> bool:
        """Check if title contains job-related keywords"""
        title_lower = title.lower()
        return any(keyword.lower() in title_lower for keyword in self.job_keywords)
        
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        # Remove extra whitespace and normalize
        cleaned = ' '.join(text.split())
        return cleaned.strip()
        
    def extract_post_data(self, post_element) -> Optional[Dict]:
        """Extract data from a single Reddit post element"""
        try:
            # Extract title
            title = post_element.get_attribute("post-title")
            if not title or not self.contains_job_keywords(title):
                return None
                
            # Extract permalink for URL construction
            permalink = post_element.get_attribute("permalink")
            full_url = f"https://www.reddit.com{permalink}" if permalink else ""
            
            # Skip if no URL (can't use as unique identifier)
            if not full_url:
                return None
            
            # Extract description from text body
            description = ""
            try:
                text_body = post_element.find_element(By.CSS_SELECTOR, 'a[slot="text-body"] div div')
                description = self.clean_text(text_body.text)
            except NoSuchElementException:
                self.logger.debug("No description found for post")
                
            # Extract timestamp
            time_posted = ""
            try:
                time_element = post_element.find_element(By.CSS_SELECTOR, 'faceplate-timeago time')
                time_posted = time_element.text
            except NoSuchElementException:
                try:
                    # Alternative selector for timestamp
                    timestamp_attr = post_element.get_attribute("created-timestamp")
                    if timestamp_attr:
                        # Convert timestamp to relative time (simplified)
                        time_posted = "Recently posted"
                except Exception:
                    self.logger.debug("No timestamp found for post")
                    
            # Extract subreddit
            subreddit = post_element.get_attribute("subreddit-prefixed-name") or ""
            
            return {
                "title": self.clean_text(title),
                "description": description,
                "time_posted": time_posted,
                "url": full_url,
                "subreddit": subreddit,
                "scraped_at": datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting post data: {e}")
            return None
            
    def scrape_subreddit(self, subreddit: str) -> List[Dict]:
        """Scrape a single subreddit for job posts"""
        url = f"https://www.reddit.com/r/{subreddit.replace('r/', '')}/"
        self.logger.info(f"Scraping subreddit: {url}")
        
        try:
            self.driver.get(url)
            
            # Wait for page to load and posts to appear
            wait = WebDriverWait(self.driver, PAGE_LOAD_TIMEOUT)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "shreddit-post")))
            
            # Additional wait to ensure content is fully loaded
            time.sleep(ADDITIONAL_LOAD_WAIT)
            
            # Find all post elements
            posts = self.driver.find_elements(By.TAG_NAME, "shreddit-post")
            self.logger.info(f"Found {len(posts)} posts in {subreddit}")
            
            job_posts = []
            for post in posts:
                try:
                    post_data = self.extract_post_data(post)
                    if post_data:
                        job_posts.append(post_data)
                        self.logger.debug(f"Extracted job post: {post_data['title'][:50]}...")
                except Exception as e:
                    self.logger.debug(f"Error processing post: {e}")
                    continue
                    
            self.logger.info(f"Extracted {len(job_posts)} job posts from {subreddit}")
            return job_posts
            
        except TimeoutException:
            self.logger.error(f"Timeout waiting for {subreddit} to load")
            return []
        except Exception as e:
            self.logger.error(f"Error scraping {subreddit}: {e}")
            return []
            
    def scrape_multiple_subreddits(self, subreddits: List[str]) -> List[Dict]:
        """Scrape multiple subreddits for job posts"""
        self.logger.info(f"Starting scrape of {len(subreddits)} subreddits")
        
        self.driver = self.setup_driver()
        all_job_posts = []
        
        try:
            for subreddit in subreddits:
                try:
                    posts = self.scrape_subreddit(subreddit)
                    all_job_posts.extend(posts)
                    
                    # Small delay between subreddit requests
                    time.sleep(DELAY_BETWEEN_SUBREDDITS)
                    
                except Exception as e:
                    self.logger.error(f"Failed to scrape {subreddit}: {e}")
                    continue
                    
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("WebDriver closed")
                
        self.logger.info(f"Total job posts extracted: {len(all_job_posts)}")
        return all_job_posts
        
    async def process_job_postings(self, job_data_list: List[Dict]) -> List[Dict]:
        """Process scraped job postings: validate, save to DB, and analyze with AI"""
        if not job_data_list:
            self.logger.warning("No job data to process")
            return []
        
        self.logger.info(f"Processing {len(job_data_list)} job postings...")
        processed_jobs = []
        new_jobs = []
        
        # Initialize database
        await self.db.init_database()
        
        # Filter out existing jobs and validate new ones
        for job_data in job_data_list:
            try:
                # Validate job posting data
                job = JobPosting(**job_data)
                
                # Check if job already exists in database
                if await self.db.job_exists(str(job.url)):
                    self.logger.debug(f"Job already exists: {job.url}")
                    continue
                
                # Insert new job into database
                job_id = await self.db.insert_job_posting(job)
                job_dict = job.dict()
                job_dict['id'] = job_id
                
                new_jobs.append(job_dict)
                processed_jobs.append(job_dict)
                
            except ValidationError as e:
                self.logger.warning(f"Invalid job data: {e}")
                continue
            except Exception as e:
                self.logger.error(f"Error processing job: {e}")
                continue
        
        self.logger.info(f"Found {len(new_jobs)} new job postings to analyze")
        
        # Analyze new jobs with AI in batches
        if new_jobs and self.ai_service:
            await self._analyze_jobs_in_batches(new_jobs)
        elif not self.ai_service:
            self.logger.warning("AI service not available - skipping analysis")
        
        return processed_jobs
    
    async def _analyze_jobs_in_batches(self, jobs: List[Dict]):
        """Analyze jobs in batches using AI service"""
        total_jobs = len(jobs)
        successful_analyses = 0
        failed_analyses = 0
        
        # Process jobs in batches
        for i in range(0, total_jobs, BATCH_SIZE):
            batch = jobs[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            total_batches = (total_jobs + BATCH_SIZE - 1) // BATCH_SIZE
            
            self.logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} jobs)")
            
            # Analyze batch
            results = await self.ai_service.analyze_job_batch(batch)
            
            # Save results to database
            for job_data, success, analysis, error in results:
                job_id = job_data['id']
                
                if success and analysis:
                    try:
                        await self.db.insert_job_analysis(job_id, analysis, OPENAI_MODEL)
                        await self.db.update_analysis_attempt(job_id, failed=False)
                        successful_analyses += 1
                        self.logger.debug(f"Analysis saved for job {job_id}")
                    except Exception as e:
                        self.logger.error(f"Error saving analysis for job {job_id}: {e}")
                        await self.db.update_analysis_attempt(job_id, failed=True, reason=str(e))
                        failed_analyses += 1
                else:
                    await self.db.update_analysis_attempt(job_id, failed=True, reason=error)
                    failed_analyses += 1
                    self.logger.warning(f"Analysis failed for job {job_id}: {error}")
            
            # Small delay between batches to avoid overwhelming the API
            if i + BATCH_SIZE < total_jobs:
                await asyncio.sleep(2)
        
        self.logger.info(f"Analysis complete: {successful_analyses} successful, {failed_analyses} failed")
        
    async def retry_failed_analyses(self):
        """Retry jobs that previously failed analysis"""
        failed_jobs = await self.db.get_failed_jobs_for_retry(MAX_RETRIES)
        
        if not failed_jobs:
            self.logger.info("No failed jobs to retry")
            return
        
        self.logger.info(f"Retrying analysis for {len(failed_jobs)} jobs")
        
        if self.ai_service:
            await self._analyze_jobs_in_batches(failed_jobs)
        
    def save_to_csv(self, job_data: List[Dict]):
        """Save job data to CSV file (legacy support)"""
        if not job_data:
            self.logger.warning("No job data to save to CSV")
            return
            
        try:
            # Convert to DataFrame and save
            df = pd.DataFrame(job_data)
            file_exists = os.path.exists(self.output_file)
            mode = 'a' if file_exists else 'w'
            header = not file_exists
            df.to_csv(self.output_file, mode=mode, header=header, index=False, encoding='utf-8')
            self.logger.info(f"Saved {len(job_data)} job posts to {self.output_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving to CSV: {e}")
            
    async def run_scrape(self, subreddits: List[str]):
        """Main method to run the scraping process with OpenAI analysis"""
        start_time = datetime.now()
        self.logger.info(f"Starting Reddit job scrape at {start_time}")
        
        try:
            # Test AI service connection
            if self.ai_service:
                ai_connected = await self.ai_service.test_connection()
                if not ai_connected:
                    self.logger.warning("AI service connection failed - continuing without analysis")
                    self.ai_service = None
            
            # Scrape all subreddits
            raw_job_posts = self.scrape_multiple_subreddits(subreddits)
            
            if raw_job_posts:
                # Process and analyze jobs
                processed_jobs = await self.process_job_postings(raw_job_posts)
                
                # Also retry any previously failed analyses
                await self.retry_failed_analyses()
                
                # Save to CSV for backward compatibility
                self.save_to_csv([job for job in raw_job_posts])
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            self.logger.info(f"Scrape completed in {duration}. Processed {len(raw_job_posts)} job posts")
            
            return raw_job_posts
            
        except Exception as e:
            self.logger.error(f"Scrape failed: {e}")
            return []


async def main():
    """Main function to run the scraper with OpenAI analysis"""
    # Configuration
    subreddits = SUBREDDITS 
    
    # Initialize scraper
    scraper = RedditJobScraper(
        output_file=OUTPUT_FILE,
        log_level=LOG_LEVEL
    )
    
    # Run scraping with analysis
    await scraper.run_scrape(subreddits)


async def scheduled_scrape():
    """Function to be called by scheduler"""
    print(f"Running scheduled scrape at {datetime.now()}")
    await main()


def start_scheduler():
    """Start the hourly scheduler"""
    print("Starting Reddit Job Scraper Scheduler...")
    print("Scraper will run every hour. Press Ctrl+C to stop.")
    
    # Wrapper function for async scheduled_scrape
    def run_scheduled_scrape():
        asyncio.run(scheduled_scrape())
    
    # Schedule the scraper to run every hour
    schedule.every(SCRAPE_INTERVAL_HOURS).hours.do(run_scheduled_scrape)
    
    # Run initial scrape
    run_scheduled_scrape()
    
    # Keep the scheduler running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\nScheduler stopped by user")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--schedule":
        start_scheduler()
    else:
        asyncio.run(main())