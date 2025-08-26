# app/main.py
"""FastAPI application for Reddit Job Scraper Dashboard"""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import uvicorn
import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from app.routers import jobs, scraper as scraper_router
from app.database import JobDatabase
from config import DATABASE_FILE

# Global database instance
db = None

async def get_db():
    """Dependency to get database instance"""
    global db
    if db is None:
        db = JobDatabase(DATABASE_FILE)
        await db.init_database()
    return db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    global db
    try:
        db = JobDatabase(DATABASE_FILE)
        await db.init_database()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
    yield
    logger.info("🔄 Shutting down application")

# Create FastAPI app
app = FastAPI(
    title="Reddit Job Scraper Dashboard",
    description="AI-powered job scraper for Reddit with intelligent filtering",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(jobs.router, prefix="/api", tags=["jobs"])# app/main.py
"""FastAPI application for Reddit Job Scraper Dashboard"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import uvicorn
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.routers import jobs, scraper as scraper_router
from app.database import JobDatabase
from config import DATABASE_FILE

# Global database instance
db = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    global db
    db = JobDatabase(DATABASE_FILE)
    await db.init_database()
    print("✅ Database initialized")
    yield
    print("🔄 Shutting down...")

# Create FastAPI app
app = FastAPI(
    title="Reddit Job Scraper Dashboard",
    description="AI-powered job scraper for Reddit with intelligent filtering",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(jobs.router, prefix="/api", tags=["jobs"])
app.include_router(scraper_router.router, prefix="/api", tags=["scraper"])

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page"""
    try:
        # Get basic stats for the dashboard
        db_instance = await get_db()
        stats = await db_instance.get_stats()
        
        return templates.TemplateResponse(
            "index.html", 
            {
                "request": request,
                "stats": stats,
                "page_title": "Dashboard"
            }
        )
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        # Return dashboard anyway with empty stats
        return templates.TemplateResponse(
            "index.html", 
            {
                "request": request,
                "stats": {"total_jobs": 0, "analyzed_jobs": 0, "worth_checking": 0, "jobs_last_24h": 0},
                "page_title": "Dashboard",
                "error": str(e)
            }
        )

@app.get("/jobs", response_class=HTMLResponse)
async def jobs_page(request: Request):
    """Jobs list page"""
    return templates.TemplateResponse(
        "jobs/list.html",
        {
            "request": request,
            "page_title": "Job Listings"
        }
    )

@app.get("/jobs/navigator", response_class=HTMLResponse)
async def jobs_navigator(request: Request):
    """Jobs card navigator page"""
    return templates.TemplateResponse(
        "jobs/card.html",
        {
            "request": request,
            "page_title": "Job Navigator"
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db_instance = await get_db()
        stats = await db_instance.get_stats()
        return {
            "status": "healthy",
            "database": "connected", 
            "total_jobs": stats.get("total_jobs", 0),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["../app", "../templates", "../static"]
    )