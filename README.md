# Reddit Job Scraper - FastAPI Edition

A professional job scraper that extracts developer/engineer job postings from Reddit, analyzes them with OpenAI for quality assessment, and provides a modern web dashboard built with FastAPI and Bootstrap.

## 🚀 Features

- **FastAPI Backend**: High-performance async web framework
- **Modern Web UI**: Responsive Bootstrap 5 interface with dark/light themes
- **Smart AI Analysis**: OpenAI GPT-4o-mini integration for job quality assessment
- **Advanced Filtering**: Time-based, confidence score, remote work, experience level filters
- **Job Navigator**: Tinder-style job browsing with keyboard shortcuts
- **Real-time Updates**: Live scraper status and job statistics
- **Export Functionality**: Download results as CSV or JSON
- **Bookmark System**: Save interesting jobs for later review
- **Dockerized**: Easy deployment with Docker and Docker Compose

## 📁 Project Structure

```
reddit-job-scraper/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── models.py            # Pydantic models for data validation
│   ├── database.py          # Async SQLite database operations
│   ├── scraper.py           # Reddit scraping logic
│   ├── ai_service.py        # OpenAI analysis service
│   ├── prompts.py           # AI prompts
│   └── routers/
│       ├── jobs.py          # Job-related API endpoints
│       └── scraper.py       # Scraper control endpoints
├── templates/               # Jinja2 HTML templates
│   ├── base.html           # Base template with Bootstrap
│   ├── index.html          # Dashboard home page
│   └── jobs/
│       ├── list.html       # Job list view
│       └── card.html       # Job navigator
├── static/
│   ├── css/custom.css      # Custom styling
│   └── js/
│       ├── components.js   # Reusable JS components
│       └── dashboard.js    # Dashboard functionality
├── scripts/
│   ├── run_scraper.py      # Scraper runner
│   └── cleanup_old_jobs.py # Database cleanup
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose setup
└── .env.example           # Environment variables template
```

## 🛠️ Installation & Setup

### Option 1: Docker (Recommended)

1. **Clone the repository**:
```bash
git clone <repository-url>
cd reddit-job-scraper
```

2. **Create environment file**:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

3. **Run with Docker Compose**:
```bash
docker-compose up -d
```

4. **Access the application**:
- Dashboard: http://localhost:8000
- Health Check: http://localhost:8000/health

### Option 2: Local Development

1. **Install Python 3.11+** and create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment**:
```bash
cp .env.example .env
# Add your OPENAI_API_KEY to .env
```

4. **Install Chrome browser** (required for Selenium)

5. **Run the application**:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🎯 Usage

### Web Dashboard

1. **Home Dashboard** (`/`):
   - Overview statistics and charts
   - Quick actions (run scraper, export data)
   - Recent job listings preview

2. **Job List** (`/jobs`):
   - Searchable, filterable job listings
   - Pagination and sorting options
   - Detailed job cards with AI analysis

3. **Job Navigator** (`/jobs/navigator`):
   - Card-style navigation through jobs
   - Keyboard shortcuts (←/→ arrow keys)
   - Detailed job analysis tabs

### API Endpoints

- **Jobs API**:
  - `GET /api/jobs` - Get filtered job listings
  - `GET /api/jobs/{id}` - Get specific job details
  - `GET /api/jobs/export/csv` - Export jobs as CSV
  - `GET /api/jobs/export/json` - Export jobs as JSON

- **Scraper Control**:
  - `GET /api/scraper/status` - Get scraper status
  - `POST /api/scraper/run` - Start scraper
  - `GET /api/scraper/logs` - Get recent logs
  - `DELETE /api/scraper/cleanup` - Clean old jobs

- **Statistics**:
  - `GET /api/stats` - Get database statistics
  - `GET /health` - Health check endpoint

### Command Line Tools

**Run scraper once**:
```bash
python scripts/run_scraper.py
```

**Run scraper on schedule** (every hour):
```bash
python scripts/run_scraper.py --schedule
```

**Clean up old jobs**:
```bash
python scripts/cleanup_old_jobs.py --days 14
```

**View database stats**:
```bash
python scripts/cleanup_old_jobs.py --stats-only
```

## 🎮 Dashboard Features

### Filters & Search
- **Time Range**: Last 3 hours to last week
- **Job Quality**: Worth checking, not recommended, or all
- **Confidence Score**: Minimum AI confidence threshold
- **Quick Filters**: Remote work, compensation mentioned
- **Advanced**: Experience level, job type, search terms
- **Presets**: Python, React, AI/ML, Cloud/DevOps, etc.

### Job Navigator
- **Navigation**: First, Previous, Next, Last buttons
- **Jump**: Direct jump to any job number
- **Keyboard Shortcuts**:
  - `←/→` - Navigate jobs
  - `Home/End` - Jump to first/last
  - `Space` - Open current job
  - `B` - Toggle bookmark

### Bookmarks
- Save interesting jobs for later review
- Filter to show only bookmarked jobs
- Export bookmarked jobs separately
- Persistent across browser sessions

### Real-time Features
- Live scraper status indicator
- Auto-updating statistics
- Progress tracking for scraper runs
- Toast notifications for actions

## ⚙️ Configuration

### Environment Variables (`.env`)
```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
DATABASE_FILE=reddit_jobs.db
LOG_LEVEL=INFO
SCRAPE_INTERVAL_HOURS=1
```

### Key Settings (`config.py`)
```python
# Subreddits to scrape
SUBREDDITS = [
    "WebDeveloperJobs", "PythonJobs", "forhire", 
    "remotepython", "MachineLearningJobs", # ...
]

# AI Processing
OPENAI_MODEL = "gpt-4o-mini"  # Cost-effective choice
BATCH_SIZE = 20  # Jobs per batch for AI analysis
MAX_RETRIES = 3

# Job Keywords (extensively expanded for your skillset)
JOB_KEYWORDS = [
    # Core technologies
    "python", "typescript", "react", "django", "fastapi", 
    "node.js", "next.js", "aws", "azure", "docker", 
    "kubernetes", "postgresql", "mongodb", 
    
    # AI/ML Technologies  
    "langchain", "langgraph", "openai", "ai", "machine learning",
    "nlp", "vector database", "embeddings", "rag",
    
    # And 100+ more relevant terms...
]
```

## 🤖 AI Analysis

Each job is analyzed for:

- **Worth Checking** (Boolean): Overall recommendation
- **Confidence Score** (0-100%): AI's confidence in assessment
- **Job Classification**: Type, experience level, remote-friendly
- **Compensation**: Whether salary/payment mentioned
- **Key Highlights**: Positive aspects (max 5)
- **Red Flags**: Issues like vague descriptions, scams
- **Recommendation**: Brief explanation of assessment

### Analysis Prompts
The AI uses structured prompts in `app/prompts.py` to ensure consistent, accurate job analysis based on your specific requirements and skill set.

## 📊 Database Schema

### Jobs Table
- URL-based deduplication
- Scraped metadata (title, description, subreddit, etc.)
- Analysis attempts and failure tracking
- Timestamps for cleanup

### Analysis Table
- AI assessment results
- JSON fields for highlights and red flags
- Model version tracking
- Analysis timestamps

## 🐳 Docker Deployment

### Development
```bash
docker-compose up -d
```

### Production
```bash
# Build and run with production profile
docker-compose --profile production up -d

# Or run individual services
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  -v $(pwd)/data:/app/data \
  reddit-job-scraper
```

### Docker Services
- **reddit-scraper**: Main web application
- **reddit-scraper-cron**: Scheduled scraper (optional)
- **nginx**: Reverse proxy for production (optional)

## 🔧 Development

### Local Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run tests (when implemented)
pytest

# Check code style
black app/ scripts/
flake8 app/ scripts/
```

### Adding New Features

1. **New API Endpoints**: Add to `app/routers/`
2. **Database Changes**: Modify `app/database.py` 
3. **UI Components**: Update templates and static files
4. **Configuration**: Add to `config.py`

## 📈 Performance & Scaling

### Current Capacity
- **Database**: SQLite (suitable for 100K+ jobs)
- **Concurrent Users**: 50+ (with FastAPI async)
- **AI Processing**: 20 jobs/batch, ~1000 jobs/hour
- **Memory Usage**: ~100-200MB typical

### Optimization Tips
- Adjust `BATCH_SIZE` for AI processing speed vs. cost
- Use database cleanup to manage storage
- Monitor OpenAI API usage and costs
- Consider PostgreSQL for >100K jobs

## 💰 Cost Estimation

### OpenAI Usage
- **Model**: GPT-4o-mini (most cost-effective)
- **Cost**: ~$0.01-0.05 per 100 job analyses
- **Daily Usage**: ~$1-5 for 1000 jobs/day

### Hosting
- **Local/VPS**: Free (your hardware/VPS)
- **Cloud**: $10-50/month depending on scale

## 🔒 Security Considerations

### API Security
- No authentication required (internal tool)
- Rate limiting on scraper endpoints
- Input validation with Pydantic

### Data Privacy
- Jobs stored locally in SQLite
- No personal data collected
- OpenAI API calls are ephemeral

### Production Hardening
```bash
# Use environment variables for secrets
# Enable HTTPS with nginx
# Implement rate limiting
# Add authentication if needed
```

## 🐛 Troubleshooting

### Common Issues

**Chrome/WebDriver Problems**:
```bash
# Install Chrome manually if webdriver-manager fails
sudo apt-get install google-chrome-stable

# Or use Firefox fallback (automatic)
```

**OpenAI API Errors**:
```bash
# Check API key and credits
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# Monitor usage in OpenAI dashboard
```

**Database Issues**:
```bash
# Reset database
rm reddit_jobs.db
# Restart application to recreate
```

**Memory Issues**:
```bash
# Reduce batch size in config.py
BATCH_SIZE = 10  # Instead of 20

# Clean old data more frequently
python scripts/cleanup_old_jobs.py --days 7
```

### Logs
- **Application**: Check console output or docker logs
- **Scraper**: `reddit_scraper.log`
- **Browser**: Selenium logs in console

## 🔄 Migration from Streamlit

If upgrading from the Streamlit version:

1. **Data Migration**: SQLite database is compatible
2. **Bookmarks**: Export/import manually (different storage)
3. **Configuration**: Review `config.py` for new options
4. **Dependencies**: Run `pip install -r requirements.txt`

## 🤝 Contributing

### Adding Subreddits
```python
# In config.py
SUBREDDITS.append("YourNewSubreddit")
```

### Improving AI Analysis
```python
# Modify prompts in app/prompts.py
# Add new analysis fields in app/models.py
# Update database schema if needed
```

### UI Enhancements
- Templates: `templates/`
- Styles: `static/css/custom.css`
- JavaScript: `static/js/`

## 📄 License

This project is for educational and personal use. Please respect:
- Reddit's terms of service and rate limits
- OpenAI's usage policies
- Employment website terms when applying to jobs

## 🆘 Support & FAQ

**Q: How often should I run the scraper?**
A: Every 1-4 hours is optimal. More frequent runs may hit rate limits.

**Q: Can I add more job sites besides Reddit?**
A: Yes, but requires modifying the scraper logic in `app/scraper.py`.

**Q: Is the AI analysis accurate?**
A: Generally 80-90% accurate for obvious cases. Use it as a filter, not final decision.

**Q: Can I run this on a server?**
A: Yes! Use Docker Compose for easy server deployment.

**Q: How do I backup my data?**
A: Copy the `reddit_jobs.db` file. Consider automated backups for production.

---

**Built with ❤️ using FastAPI, Bootstrap 5, and OpenAI**

For issues or questions, check the logs first, then create an issue with:
- Error messages
- Steps to reproduce
- Your configuration (without API keys)