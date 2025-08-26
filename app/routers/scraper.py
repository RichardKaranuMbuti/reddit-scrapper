# app/routers/scraper.py
"""API endpoints for scraper control and status"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime
import asyncio
import os
import sys

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.models import ScraperStatus
from app.scrapper import RedditJobScraper
from config import SUBREDDITS, OUTPUT_FILE, LOG_LEVEL

router = APIRouter()

# Global scraper state
scraper_state = {
    "is_running": False,
    "last_run": None,
    "jobs_scraped_last_run": None,
    "current_task": None
}

async def run_scraper_task():
    """Background task to run the scraper"""
    global scraper_state
    
    try:
        scraper_state["is_running"] = True
        scraper_state["last_run"] = datetime.now()
        
        # Initialize and run scraper
        scraper = RedditJobScraper(
            output_file=OUTPUT_FILE,
            log_level=LOG_LEVEL
        )
        
        results = await scraper.run_scrape(SUBREDDITS)
        scraper_state["jobs_scraped_last_run"] = len(results) if results else 0
        
    except Exception as e:
        print(f"Scraper task failed: {e}")
        scraper_state["jobs_scraped_last_run"] = 0
    finally:
        scraper_state["is_running"] = False
        scraper_state["current_task"] = None

@router.get("/scraper/status", response_model=ScraperStatus)
async def get_scraper_status():
    """Get current scraper status"""
    return ScraperStatus(
        is_running=scraper_state["is_running"],
        last_run=scraper_state["last_run"],
        jobs_scraped_last_run=scraper_state["jobs_scraped_last_run"],
        next_scheduled_run=None  # We're not implementing scheduler in API for now
    )

@router.post("/scraper/run")
async def run_scraper(background_tasks: BackgroundTasks):
    """Start a scraper run"""
    global scraper_state
    
    if scraper_state["is_running"]:
        raise HTTPException(status_code=400, detail="Scraper is already running")
    
    # Start scraper as background task
    background_tasks.add_task(run_scraper_task)
    
    return {
        "message": "Scraper started successfully",
        "status": "running",
        "started_at": datetime.now().isoformat()
    }

@router.post("/scraper/stop")
async def stop_scraper():
    """Stop the scraper (if possible)"""
    global scraper_state
    
    if not scraper_state["is_running"]:
        raise HTTPException(status_code=400, detail="Scraper is not currently running")
    
    # Note: This is a simple implementation
    # In production, you'd want proper task cancellation
    if scraper_state["current_task"]:
        scraper_state["current_task"].cancel()
    
    scraper_state["is_running"] = False
    
    return {
        "message": "Scraper stop requested",
        "status": "stopped"
    }

@router.get("/scraper/logs")
async def get_scraper_logs(lines: int = 50):
    """Get recent scraper logs"""
    try:
        log_file = "reddit_scraper.log"
        if not os.path.exists(log_file):
            return {"logs": [], "message": "No log file found"}
        
        with open(log_file, 'r') as f:
            log_lines = f.readlines()
        
        # Get last N lines
        recent_logs = log_lines[-lines:] if len(log_lines) > lines else log_lines
        
        return {
            "logs": [line.strip() for line in recent_logs],
            "total_lines": len(log_lines),
            "showing_lines": len(recent_logs)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading logs: {str(e)}")

@router.delete("/scraper/cleanup")
async def cleanup_old_jobs(days: int = 14):
    """Clean up old job postings"""
    try:
        from app.database import JobDatabase
        from config import DATABASE_FILE
        
        db = JobDatabase(DATABASE_FILE)
        deleted_count = await db.cleanup_old_jobs(days)
        
        return {
            "message": f"Cleanup completed successfully",
            "deleted_jobs": deleted_count,
            "retention_days": days
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during cleanup: {str(e)}")