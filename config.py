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
    # Core job terms
    "developer", "[hiring]", "engineer", "full stack", "backend", 
    "frontend", "software", "programmer", "coding", "remote", 
    "freelance", "devops", "data scientist", "machine learning",
    "software engineer", "web developer", "senior developer", "junior developer",
    "tech lead", "architect", "consultant", "contractor",
    
    # Languages (your skillset)
    "python", "java", "typescript", "javascript", "react", "react.js",
    "django", "spring boot", "node.js", "nodejs", "fastapi", "next.js",
    "nextjs", "go", "golang", "sql", "nosql",
    
    # Frameworks & Technologies
    "express", "express.js", "nestjs", "nest.js", "spring", "flask",
    "vue", "vue.js", "angular", "svelte", "tailwind", "bootstrap",
    
    # Infrastructure & DevOps (your skillset)
    "aws", "azure", "docker", "kubernetes", "k8s", "ci/cd", "jenkins",
    "microservices", "postgresql", "postgres", "mongodb", "mongo",
    "redis", "linux", "git", "github", "gitlab", "terraform",
    "ansible", "helm", "nginx", "apache",
    
    # Databases
    "mysql", "sqlite", "elasticsearch", "dynamodb", "cassandra",
    "database", "dba", "data engineer", "etl",
    
    # AI & ML (your emerging tech)
    "ai", "artificial intelligence", "machine learning", "ml", "nlp",
    "langchain", "langgraph", "langsmith", "openai", "gpt", "llm",
    "langfuse", "vector database", "embeddings", "rag", "chatbot",
    "ai agent", "agentic", "prompt engineering", "fine tuning",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    
    # Cloud & Services
    "gcp", "google cloud", "firebase", "vercel", "netlify", "heroku",
    "digitalocean", "linode", "cloudflare", "serverless", "lambda",
    "azure functions", "cloud functions", "api gateway", "s3",
    
    # Testing & Quality
    "tdd", "test driven", "pytest", "jest", "cypress", "selenium",
    "unit test", "integration test", "automation", "qa", "quality assurance",
    
    # Authentication & Security
    "jwt", "oauth", "auth0", "keycloak", "security", "encryption",
    "ssl", "https", "authentication", "authorization",
    
    # Tools & Platforms
    "celery", "redis", "rabbitmq", "kafka", "elasticsearch", "grafana",
    "prometheus", "datadog", "sentry", "stripe", "payment", "api",
    "rest api", "graphql", "grpc", "websocket", "socket.io",
    
    # Mobile & Cross-platform
    "mobile", "ios", "android", "react native", "flutter", "ionic",
    "xamarin", "cordova", "phonegap", "swift", "kotlin",
    
    # Blockchain & Web3 (emerging)
    "blockchain", "web3", "ethereum", "solidity", "smart contract",
    "defi", "nft", "crypto", "bitcoin", "polygon", "solana",
    
    # Specific roles that might be relevant
    "technical lead", "team lead", "staff engineer", "principal engineer",
    "solutions architect", "platform engineer", "site reliability",
    "sre", "product engineer", "growth engineer", "founding engineer",
    
    # Work arrangements
    "part time", "contract", "consulting", "startup", "agency",
    "b2b", "saas", "fintech", "edtech", "healthtech", "proptech",
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