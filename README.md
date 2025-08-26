# Reddit Job Scraper with AI Analysis

An intelligent job scraper that extracts developer/engineer job postings from Reddit, analyzes them with OpenAI for quality assessment, and provides a beautiful Streamlit dashboard for filtering and viewing results.

## 🚀 Features

- **Smart Web Scraping**: Scrapes multiple programming-related subreddits
- **AI-Powered Analysis**: Uses OpenAI GPT-4o-mini to assess job quality
- **Duplicate Detection**: Uses URL-based deduplication to avoid processing the same job twice
- **Batch Processing**: Processes jobs in configurable batches for efficient API usage
- **SQLite Database**: Stores all data with proper indexing for fast queries
- **Real-time Dashboard**: Beautiful Streamlit UI for filtering and viewing jobs
- **Scheduled Execution**: Can run automatically every hour
- **Robust Error Handling**: Exponential backoff for API failures and graceful degradation

## 📋 Requirements

- Python 3.8+
- Chrome browser (for Selenium)
- OpenAI API key

## 🛠️ Installation

1. **Clone or download the files** and navigate to the directory:

```bash
cd reddit-job-scraper
```

2. **Install required packages**:

```bash
pip install -r requirements.txt
```

3. **Create a `.env` file** with your OpenAI API key:

```bash
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

4. **Configure settings** in `config.py`:
   - Add/remove subreddits to scrape
   - Adjust batch size for AI processing
   - Modify time filters and other settings

## 🎯 Usage

### Quick Start

1. **Run the scraper once**:
```bash
python run_scraper.py
```

2. **Start the dashboard**:
```bash
python run_dashboard.py
```

3. **Open your browser** to `http://localhost:8501` to view the dashboard

### Advanced Usage

**Schedule automatic scraping** (runs every hour):
```bash
python run_scraper.py --schedule
```

**Clean up old job postings**:
```bash
python cleanup_old_jobs.py --days 14
```

**View database statistics**:
```bash
python cleanup_old_jobs.py --stats-only
```

## 📊 Dashboard Features

The Streamlit dashboard provides:

### Filters
- **Time Range**: Last 3 hours, 5 hours, 24 hours, 3 days, or week
- **Job Quality**: All jobs, worth checking only, or not worth checking
- **Confidence Score**: Minimum AI confidence threshold
- **Remote Work**: Filter for remote-friendly positions
- **Compensation**: Filter for jobs mentioning salary
- **Experience Level**: Entry, mid, senior, lead, or unspecified
- **Job Type**: Full-time, part-time, contract, freelance, internship

### Views
- **Analytics Tab**: Charts and distributions of job data
- **Job List Tab**: Searchable, sortable list of job postings with AI analysis
- **Trends Tab**: Historical trends over time

### Export Options
- Download filtered results as CSV or JSON
- Real-time data refresh

## 🤖 AI Analysis

Each job posting is analyzed for:

- **Worth Checking**: Boolean recommendation
- **Confidence Score**: 0-100% confidence in the assessment
- **Job Type**: Full-time, contract, freelance, etc.
- **Compensation**: Whether salary/payment is mentioned
- **Remote Friendly**: Supports remote work
- **Experience Level**: Required experience level
- **Red Flags**: Issues like vague descriptions, possible scams
- **Key Highlights**: Positive aspects of the posting
- **Recommendation**: Brief AI recommendation

## 📁 File Structure

```
├── config.py              # Configuration settings
├── schemas.py             # Pydantic data models
├── prompts.py             # AI prompts for analysis
├── database.py            # SQLite database operations
├── ai_service.py          # OpenAI analysis service
├── scrapper.py            # Main scraper (updated)
├── streamlit_app.py       # Dashboard UI
├── cleanup_old_jobs.py    # Database cleanup script
├── run_scraper.py         # Scraper runner script
├── run_dashboard.py       # Dashboard runner script
├── requirements.txt       # Python dependencies
└── .env                   # Environment variables (create this)
```

## ⚙️ Configuration Options

### Key Settings in `config.py`:

- `SUBREDDITS`: List of subreddits to scrape
- `BATCH_SIZE`: Number of jobs to analyze simultaneously (default: 20)
- `OPENAI_MODEL`: AI model to use (default: "gpt-4o-mini" for cost efficiency)
- `MAX_RETRIES`: Number of retry attempts for failed analyses
- `JOB_RETENTION_DAYS`: How long to keep jobs in database (default: 14 days)

### Environment Variables:

- `OPENAI_API_KEY`: Your OpenAI API key (required)

## 🔧 Troubleshooting

### Common Issues:

1. **Chrome WebDriver Issues**:
   - Install Chrome browser
   - The script will auto-download ChromeDriver via webdriver-manager
   - If issues persist, try Firefox as fallback

2. **OpenAI API Errors**:
   - Verify your API key is correct
   - Check you have sufficient API credits
   - The script uses exponential backoff for rate limits

3. **Database Errors**:
   - Ensure write permissions in the directory
   - Database will be created automatically on first run

4. **Memory Issues with Large Batches**:
   - Reduce `BATCH_SIZE` in config.py
   - Consider increasing system memory

### Logs:

Check `reddit_scraper.log` for detailed error information.

## 💰 Cost Optimization

The scraper is optimized for cost efficiency:

- Uses GPT-4o-mini (cheapest OpenAI model suitable for this task)
- Batch processing reduces API overhead
- Duplicate detection prevents reprocessing
- Configurable retry limits prevent excessive API calls

Estimated cost: ~$0.01-0.05 per 100 job analyses.

## 🔄 Automation

For continuous operation:

1. **Use the built-in scheduler**:
```bash
python run_scraper.py --schedule
```

2. **Or set up a system cron job** (Linux/Mac):
```bash
# Run every hour
0 * * * * /path/to/python /path/to/run_scraper.py

# Clean up old jobs daily
0 2 * * * /path/to/python /path/to/cleanup_old_jobs.py
```

3. **Or use Windows Task Scheduler** for Windows systems.

## 📈 Performance Tips

- **Database Performance**: Indexes are created automatically for fast queries
- **Scraping Performance**: Adjust delays in config.py if getting blocked
- **API Performance**: Monitor OpenAI usage and adjust batch size if needed
- **UI Performance**: Dashboard caches data for 1-5 minutes to reduce database load

## 🤝 Contributing

Feel free to:
- Add more subreddits to the configuration
- Improve the AI prompts for better analysis
- Enhance the dashboard with additional features
- Add new filtering options
- Optimize the scraping logic

## 📄 License

This project is for educational and personal use. Respect Reddit's terms of service and rate limiting. Use responsibly.

## 🆘 Support

If you encounter issues:
1. Check the logs in `reddit_scraper.log`
2. Verify your `.env` file has the correct OpenAI API key
3. Ensure Chrome browser is installed
4. Check that all dependencies are installed correctly

For advanced usage or customization, refer to the inline code documentation.