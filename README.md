# Reddit Job Scraper

A Python-based web scraper that extracts developer/engineering job posts from specified Reddit subreddits and saves them to a CSV file.

## Features

- Scrapes multiple subreddits for job-related posts
- Filters posts based on job keywords (developer, engineer, hiring, etc.)
- Extracts title, description, posting time, and URL
- Saves data to CSV with timestamps
- Comprehensive logging
- Hourly scheduling capability
- Modular and maintainable code structure

## Setup

### Prerequisites

- Python 3.7+
- Chrome browser installed
- ChromeDriver (will be installed automatically with selenium)

### Installation

1. Create and activate a virtual environment:
```bash
python -m venv reddit_scraper_env
source reddit_scraper_env/bin/activate  # On Windows: reddit_scraper_env\Scripts\activate
```

2. Install dependencies:
```bash
pip install requests beautifulsoup4 selenium pandas schedule python-dotenv lxml
```

3. Save the scraper code as `reddit_scraper.py`

## Usage

### One-time Scrape
```bash
python reddit_scraper.py
```

### Scheduled Hourly Scraping
```bash
python reddit_scraper.py --schedule
```

### Customizing Subreddits

Edit the `subreddits` list in the `main()` function:

```python
subreddits = [
    "WebDeveloperJobs",
    "AppDevelopers", 
    "forhire",
    # Add more subreddits here
]
```

### Customizing Job Keywords

Modify the `job_keywords` list in the `RedditJobScraper` class:

```python
self.job_keywords = ["developer", "[hiring]", "engineer", "full stack", "backend"]
```

## Output

The scraper creates two files:

1. **reddit_jobs.csv** - Contains scraped job data with columns:
   - title
   - description  
   - time_posted
   - url
   - subreddit
   - scraped_at

2. **reddit_scraper.log** - Contains detailed logging information

## Configuration Options

You can customize the scraper by modifying these parameters in the `RedditJobScraper` class:

- `output_file`: CSV output filename
- `job_keywords`: Keywords to filter job posts
- `log_level`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)

## Troubleshooting

### Common Issues

1. **ChromeDriver not found**: The scraper uses selenium-manager to automatically download ChromeDriver, but if you encounter issues, manually download ChromeDriver and add it to your PATH.

2. **Timeout errors**: Reddit pages may load slowly. Increase the timeout in the `scrape_subreddit` method:
   ```python
   wait = WebDriverWait(self.driver, 30)  # Increase from 15 to 30 seconds
   ```

3. **No posts found**: Some subreddits may have different HTML structures. Check the logs for details and consider updating the CSS selectors.

4. **Rate limiting**: If you encounter rate limiting, increase the delay between requests:
   ```python
   time.sleep(5)  # Increase from 2 to 5 seconds
   ```

### Debugging

Enable debug logging to see detailed information:

```python
scraper = RedditJobScraper(log_level="DEBUG")
```

## Legal and Ethical Considerations

- This scraper is for educational and personal use
- Respect Reddit's robots.txt and terms of service
- Use reasonable delays between requests
- Don't overload Reddit's servers
- Consider using Reddit's official API for production use

## Scheduling

The scraper includes built-in scheduling functionality. When run with `--schedule`, it will:

1. Run an initial scrape immediately
2. Schedule subsequent scrapes every hour
3. Continue running until manually stopped (Ctrl+C)

## Output Example

```csv
title,description,time_posted,url,subreddit,scraped_at
"Looking for an app developer, for long term projects","I run a bootstrapped software studio, where we build apps for clients and inhouse apps as well. I'm looking for a builder...","10 days ago","https://www.reddit.com/r/AppDevelopers/comments/1m9n7nc/looking_for_an_app_developer_for_long_term/","r/AppDevelopers","2025-08-05T10:30:00.123456"
```