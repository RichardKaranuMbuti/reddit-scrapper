import requests
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
from openai import AsyncOpenAI
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class RedditJobScraper:
    """Reddit job scraper for extracting developer/engineer job posts with OpenAI analysis"""
    
    def __init__(self, output_file: str = "reddit_jobs.csv", analyzed_file: str = "analyzed_jobs.csv", log_level: str = "INFO"):
        self.output_file = output_file
        self.analyzed_file = analyzed_file
        self.job_keywords = ["developer", "[hiring]", "engineer", "full stack", "backend", "frontend", "software"]
        self.setup_logging(log_level)
        self.driver = None
        
        # OpenAI setup
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        if not os.getenv("OPENAI_API_KEY"):
            self.logger.warning("OPENAI_API_KEY not found. Analysis will be skipped.")
            self.openai_client = None
        
    def setup_logging(self, log_level: str):
        """Setup logging configuration"""
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format,
            handlers=[
                logging.FileHandler("reddit_scraper.log"),
                logging.StreamHandler()
            ]
        )
            
    async def analyze_job_posting(self, job_data: Dict) -> Optional[Dict]:
        """Analyze a job posting using OpenAI to determine if it's worth checking"""
        if not self.openai_client:
            return None
            
        system_prompt = """
        You are analyzing Reddit job postings for a developer/engineer looking for legitimate job opportunities.
        
        Analyze the posting and determine if it's worth the user's time to check based on:
        1. Is the poster actually hiring (not just asking for advice or discussing jobs)?
        2. Is it a legitimate job opportunity (not spam, not selling courses, not MLM)?
        3. Does it offer reasonable compensation or mention paid work?
        4. Is it for developer/engineer/programming roles?
        5. Does it provide enough detail to be taken seriously?
        
        Return your analysis as JSON with this exact schema:
        {
            "worth_checking": boolean,
            "confidence_score": number (0-100),
            "job_type": string,
            "compensation_mentioned": boolean,
            "remote_friendly": boolean,
            "experience_level": string,
            "red_flags": array of strings,
            "key_highlights": array of strings,
            "recommendation": string
        }
        """
        
        user_prompt = f"""
        REDDIT JOB POSTING ANALYSIS
        
        Title: {job_data.get('title', 'N/A')}
        Subreddit: {job_data.get('subreddit', 'N/A')}
        Time Posted: {job_data.get('time_posted', 'N/A')}
        
        Description:
        {job_data.get('description', 'No description available')}
        
        Please analyze this posting and return your assessment in the required JSON format.
        """
        
        try:
            self.logger.debug(f"Analyzing job posting: {job_data.get('title', 'Unknown')[:50]}...")
            
            completion = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Using mini for cost efficiency
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            response_content = completion.choices[0].message.content.strip()
            
            # Try to extract JSON from response
            try:
                # Find JSON in the response
                json_start = response_content.find('{')
                json_end = response_content.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_str = response_content[json_start:json_end]
                    analysis = json.loads(json_str)
                    
                    # Add metadata
                    analysis['analyzed_at'] = datetime.now().isoformat()
                    analysis['model_used'] = 'gpt-4o-mini'
                    
                    self.logger.debug(f"Analysis complete: Worth checking = {analysis.get('worth_checking', False)}")
                    return analysis
                else:
                    self.logger.warning("No valid JSON found in OpenAI response")
                    return None
                    
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse OpenAI response as JSON: {e}")
                self.logger.debug(f"Raw response: {response_content}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error analyzing job posting with OpenAI: {e}")
            return None
        
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
                "scraped_at": datetime.now().isoformat()
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
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "shreddit-post")))
            
            # Additional wait to ensure content is fully loaded
            time.sleep(3)
            
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
                    time.sleep(2)
                    
                except Exception as e:
                    self.logger.error(f"Failed to scrape {subreddit}: {e}")
                    continue
                    
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("WebDriver closed")
                
        self.logger.info(f"Total job posts extracted: {len(all_job_posts)}")
        return all_job_posts
        
    def save_to_csv(self, job_data: List[Dict]):
        """Save job data to CSV file"""
        if not job_data:
            self.logger.warning("No job data to save")
            return
            
        try:
            # Prepare data for CSV (flatten AI analysis)
            csv_data = []
            analyzed_data = []
            
            for post in job_data:
                # Original post data for main CSV
                csv_row = {
                    'title': post.get('title', ''),
                    'description': post.get('description', ''),
                    'time_posted': post.get('time_posted', ''),
                    'url': post.get('url', ''),
                    'subreddit': post.get('subreddit', ''),
                    'scraped_at': post.get('scraped_at', '')
                }
                csv_data.append(csv_row)
                
                # Analyzed data for analyzed CSV (only if analysis exists)
                if 'ai_analysis' in post:
                    analysis = post['ai_analysis']
                    analyzed_row = {
                        **csv_row,  # Include all original data
                        'worth_checking': analysis.get('worth_checking', False),
                        'confidence_score': analysis.get('confidence_score', 0),
                        'job_type': analysis.get('job_type', ''),
                        'compensation_mentioned': analysis.get('compensation_mentioned', False),
                        'remote_friendly': analysis.get('remote_friendly', False),
                        'experience_level': analysis.get('experience_level', ''),
                        'red_flags': '; '.join(analysis.get('red_flags', [])),
                        'key_highlights': '; '.join(analysis.get('key_highlights', [])),
                        'recommendation': analysis.get('recommendation', ''),
                        'analyzed_at': analysis.get('analyzed_at', ''),
                        'model_used': analysis.get('model_used', '')
                    }
                    analyzed_data.append(analyzed_row)
            
            # Save main CSV (all posts)
            df = pd.DataFrame(csv_data)
            file_exists = os.path.exists(self.output_file)
            mode = 'a' if file_exists else 'w'
            header = not file_exists
            df.to_csv(self.output_file, mode=mode, header=header, index=False, encoding='utf-8')
            self.logger.info(f"Saved {len(csv_data)} job posts to {self.output_file}")
            
            # Save analyzed CSV (only analyzed posts)
            if analyzed_data:
                df_analyzed = pd.DataFrame(analyzed_data)
                file_exists_analyzed = os.path.exists(self.analyzed_file)
                mode_analyzed = 'a' if file_exists_analyzed else 'w'
                header_analyzed = not file_exists_analyzed
                df_analyzed.to_csv(self.analyzed_file, mode=mode_analyzed, header=header_analyzed, index=False, encoding='utf-8')
                self.logger.info(f"Saved {len(analyzed_data)} analyzed posts to {self.analyzed_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving to CSV: {e}")
            
    async def run_scrape(self, subreddits: List[str]):
        """Main method to run the scraping process with OpenAI analysis"""
        start_time = datetime.now()
        self.logger.info(f"Starting Reddit job scrape at {start_time}")
        
        try:
            # Scrape all subreddits
            job_posts = self.scrape_multiple_subreddits(subreddits)
            
            if job_posts:
                # Process with OpenAI analysis
                analyzed_posts = await self.process_job_postings(job_posts)
                
                # Save to CSV files
                self.save_to_csv(analyzed_posts)
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            self.logger.info(f"Scrape completed in {duration}. Found {len(job_posts)} job posts")
            
            return job_posts
            
        except Exception as e:
            self.logger.error(f"Scrape failed: {e}")
            return []

from config import SUBREDDITS
async def main():
    """Main function to run the scraper with OpenAI analysis"""
    # Configuration
    subreddits = SUBREDDITS 
    # Initialize scraper
    scraper = RedditJobScraper(
        output_file="reddit_jobs.csv",
        analyzed_file="analyzed_jobs.csv"
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
    schedule.every().hour.do(run_scheduled_scrape)
    
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