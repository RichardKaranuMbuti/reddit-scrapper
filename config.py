# config.py
"""Configuration file for Reddit Job Scraper"""

# Subreddits to scrape (without r/ prefix)
SUBREDDITS = [
    "WebDeveloperJobs",
    "AppDevelopers", 
    "forhire",
    "PythonJobs",
    "cofounders",
    "BigDataJobs",
    "remotepython",
    "MachineLearningJobs",
    "WebDeveloperJobs",
]

# Job-related keywords to filter posts
JOB_KEYWORDS = [
    "developer",
    "[hiring]", 
    "engineer",
    "full stack",
    "backend",
    "frontend",
    "software",
    "programmer",
    "coding",
    "remote",
    "freelance"
]

# Output settings
OUTPUT_FILE = "reddit_jobs.csv"
LOG_FILE = "reddit_scraper.log"
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR

# Scraping settings
PAGE_LOAD_TIMEOUT = 15  # seconds
DELAY_BETWEEN_SUBREDDITS = 2  # seconds
ADDITIONAL_LOAD_WAIT = 3  # seconds

# Scheduler settings
SCRAPE_INTERVAL_HOURS = 1