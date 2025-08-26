
# run_scraper.py
#!/usr/bin/env python3
"""Runner script for the job scraper"""

import asyncio
import sys
import os
from datetime import datetime

# Add current directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapper import RedditJobScraper, start_scheduler
from config import SUBREDDITS, OUTPUT_FILE, LOG_LEVEL

def print_usage():
    """Print usage information"""
    print("""
Reddit Job Scraper Usage:

Commands:
  python run_scraper.py              - Run scraper once
  python run_scraper.py --schedule   - Run scraper on schedule (every hour)  
  python run_scraper.py --help       - Show this help message

The scraper will:
1. Scrape job postings from configured subreddits
2. Analyze them with OpenAI for quality assessment
3. Store results in SQLite database
4. Also save to CSV for backward compatibility

Make sure to:
- Set OPENAI_API_KEY in your .env file
- Install Chrome browser for Selenium
- Install required Python packages: pip install -r requirements.txt
""")

async def run_once():
    """Run the scraper once"""
    print(f"Starting single scrape run at {datetime.now()}")
    print(f"Configured subreddits: {', '.join(SUBREDDITS)}")
    
    scraper = RedditJobScraper(
        output_file=OUTPUT_FILE,
        log_level=LOG_LEVEL
    )
    
    try:
        results = await scraper.run_scrape(SUBREDDITS)
        print(f"Scrape completed successfully. Found {len(results)} job posts.")
        print("Check the Streamlit dashboard to view analyzed results.")
        
    except Exception as e:
        print(f"Scrape failed: {e}")
        sys.exit(1)

def main():
    """Main function"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--schedule":
            print("Starting scheduled scraper...")
            start_scheduler()
        elif sys.argv[1] in ["--help", "-h"]:
            print_usage()
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print_usage()
            sys.exit(1)
    else:
        # Run once
        asyncio.run(run_once())

if __name__ == "__main__":
    main()