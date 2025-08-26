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
]

# Job-related keywords to filter posts
JOB_KEYWORDS = [
    "developer", "[hiring]", "engineer", "full stack", "backend", 
    "frontend", "software", "programmer", "coding", "remote", 
    "freelance", "devops", "data scientist", "machine learning"
]

# Output settings
OUTPUT_FILE = "reddit_jobs.csv"
LOG_FILE = "reddit_scraper.log"
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR

# Database settings
DATABASE_FILE = "reddit_jobs.db"
JOB_RETENTION_DAYS = 14

# Scraping settings
PAGE_LOAD_TIMEOUT = 15  # seconds
DELAY_BETWEEN_SUBREDDITS = 2  # seconds
ADDITIONAL_LOAD_WAIT = 3  # seconds

# OpenAI settings
OPENAI_MODEL = "gpt-4o-mini"  # Cheapest and most effective for this task
BATCH_SIZE = 20  # Process jobs in batches
MAX_RETRIES = 3
RETRY_DELAY = 1  # Base delay for exponential backoff

# Scheduler settings
SCRAPE_INTERVAL_HOURS = 1

# Streamlit UI settings
DEFAULT_TIME_FILTERS = [
    ("Last 3 hours", 3),
    ("Last 5 hours", 5), 
    ("Last 24 hours", 24),
    ("Last 3 days", 72),
    ("Last week", 168)
]