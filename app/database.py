# database.py
"""Database operations for Reddit job scraper"""
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
import aiosqlite
from app.models import JobPosting, AnalyzedJobPosting, JobPostingAnalysis
from config import DATABASE_FILE, JOB_RETENTION_DAYS

logger = logging.getLogger(__name__)


class JobDatabase:
    """Async database operations for job postings"""
    
    def __init__(self, db_path: str = DATABASE_FILE):
        self.db_path = db_path
        
    async def init_database(self):
        """Initialize database with required tables"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS job_postings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    time_posted TEXT,
                    time_posted_parsed TIMESTAMP,  -- Add parsed timestamp
                    subreddit TEXT NOT NULL,
                    scraped_at TIMESTAMP NOT NULL,
                    analysis_attempts INTEGER DEFAULT 0,
                    last_analysis_attempt TIMESTAMP,
                    analysis_failed BOOLEAN DEFAULT FALSE,
                    failure_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS job_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    worth_checking BOOLEAN NOT NULL,
                    confidence_score REAL NOT NULL,
                    job_type TEXT,
                    compensation_mentioned BOOLEAN NOT NULL,
                    remote_friendly BOOLEAN NOT NULL,
                    experience_level TEXT,
                    red_flags TEXT, -- JSON array
                    key_highlights TEXT, -- JSON array
                    recommendation TEXT,
                    analyzed_at TIMESTAMP NOT NULL,
                    model_used TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES job_postings (id) ON DELETE CASCADE
                )
            ''')
            
            # Create indexes for better performance
            await db.execute('CREATE INDEX IF NOT EXISTS idx_job_url ON job_postings(url)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_job_scraped_at ON job_postings(scraped_at)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_analysis_worth_checking ON job_analysis(worth_checking)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_analysis_analyzed_at ON job_analysis(analyzed_at)')
            
            await db.commit()
            logger.info("Database initialized successfully")
    
    async def job_exists(self, url: str) -> bool:
        """Check if a job posting already exists by URL"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT 1 FROM job_postings WHERE url = ? LIMIT 1', (url,))
            result = await cursor.fetchone()
            return result is not None
    
    async def insert_job_posting(self, job: JobPosting) -> int:
        """Insert a new job posting with parsed time, return job_id"""
        from app.utils import parse_reddit_time
        
        # Parse the time_posted string
        parsed_time = parse_reddit_time(job.time_posted)
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO job_postings 
                (url, title, description, time_posted, time_posted_parsed, subreddit, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(job.url), job.title, job.description, 
                job.time_posted, parsed_time, job.subreddit, job.scraped_at
            ))
            await db.commit()
            return cursor.lastrowid
    
    async def insert_job_analysis(self, job_id: int, analysis: JobPostingAnalysis, model_used: str):
        """Insert job analysis results"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO job_analysis 
                (job_id, worth_checking, confidence_score, job_type, compensation_mentioned,
                 remote_friendly, experience_level, red_flags, key_highlights, 
                 recommendation, analyzed_at, model_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_id, analysis.worth_checking, analysis.confidence_score,
                analysis.job_type.value, analysis.compensation_mentioned,
                analysis.remote_friendly, analysis.experience_level.value,
                json.dumps([flag.value for flag in analysis.red_flags]),
                json.dumps(analysis.key_highlights),
                analysis.recommendation, datetime.now(), model_used
            ))
            await db.commit()
    
    async def update_analysis_attempt(self, job_id: int, failed: bool = False, reason: str = None):
        """Update analysis attempt information"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE job_postings 
                SET analysis_attempts = analysis_attempts + 1,
                    last_analysis_attempt = ?,
                    analysis_failed = ?,
                    failure_reason = ?,
                    updated_at = ?
                WHERE id = ?
            ''', (datetime.now(), failed, reason, datetime.now(), job_id))
            await db.commit()
    
    async def get_unanalyzed_jobs(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get job postings that haven't been analyzed yet"""
        query = '''
            SELECT jp.id, jp.url, jp.title, jp.description, jp.time_posted, 
                   jp.subreddit, jp.scraped_at, jp.analysis_attempts, jp.analysis_failed
            FROM job_postings jp
            LEFT JOIN job_analysis ja ON jp.id = ja.job_id
            WHERE ja.job_id IS NULL 
            AND jp.analysis_failed = FALSE
            ORDER BY jp.scraped_at DESC
        '''
        
        if limit:
            query += f' LIMIT {limit}'
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_failed_jobs_for_retry(self, max_attempts: int = 3) -> List[Dict[str, Any]]:
        """Get jobs that failed analysis and can be retried"""
        query = '''
            SELECT jp.id, jp.url, jp.title, jp.description, jp.time_posted, 
                   jp.subreddit, jp.scraped_at, jp.analysis_attempts
            FROM job_postings jp
            LEFT JOIN job_analysis ja ON jp.id = ja.job_id
            WHERE ja.job_id IS NULL 
            AND jp.analysis_attempts < ?
            AND jp.last_analysis_attempt < datetime('now', '-1 hour')
            ORDER BY jp.analysis_attempts ASC, jp.last_analysis_attempt ASC
        '''
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, (max_attempts,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_analyzed_jobs(self, hours_back: int = 24, worth_checking_only: bool = False) -> List[Dict[str, Any]]:
        """Get analyzed job postings within time frame, sorted by recency"""
        time_threshold = datetime.now() - timedelta(hours=hours_back)
        
        query = '''
            SELECT jp.id, jp.url, jp.title, jp.description, jp.time_posted, 
                   jp.time_posted_parsed, jp.subreddit, jp.scraped_at,
                   ja.worth_checking, ja.confidence_score, ja.job_type,
                   ja.compensation_mentioned, ja.remote_friendly, ja.experience_level,
                   ja.red_flags, ja.key_highlights, ja.recommendation, ja.analyzed_at
            FROM job_postings jp
            JOIN job_analysis ja ON jp.id = ja.job_id
            WHERE jp.scraped_at > ?
        '''
        
        params = [time_threshold]
        
        if worth_checking_only:
            query += ' AND ja.worth_checking = TRUE'
        
        # Sort by parsed time if available, otherwise by scraped time
        query += '''
            ORDER BY 
                CASE 
                    WHEN jp.time_posted_parsed IS NOT NULL THEN jp.time_posted_parsed 
                    ELSE jp.scraped_at 
                END DESC
        '''
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            
            # Parse JSON fields and add time priority
            results = []
            for row in rows:
                row_dict = dict(row)
                if row_dict['red_flags']:
                    row_dict['red_flags'] = json.loads(row_dict['red_flags'])
                else:
                    row_dict['red_flags'] = []
                    
                if row_dict['key_highlights']:
                    row_dict['key_highlights'] = json.loads(row_dict['key_highlights'])
                else:
                    row_dict['key_highlights'] = []
                
                # Add time priority for sorting
                from app.utils import calculate_time_priority, format_time_ago
                row_dict['time_priority'] = calculate_time_priority(row_dict.get('time_posted', ''))
                row_dict['formatted_time'] = format_time_ago(row_dict.get('time_posted', ''))
                    
                results.append(row_dict)
            
            # Sort by time priority (most recent first)
            from app.utils import sort_jobs_by_recency
            results = sort_jobs_by_recency(results, 'time_posted')
            
            return results
    
    async def cleanup_old_jobs(self, retention_days: int = JOB_RETENTION_DAYS) -> int:
        """Remove job postings older than retention period"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                DELETE FROM job_postings 
                WHERE scraped_at < ?
            ''', (cutoff_date,))
            await db.commit()
            
            deleted_count = cursor.rowcount
            logger.info(f"Cleaned up {deleted_count} job postings older than {retention_days} days")
            return deleted_count
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # Total jobs
            cursor = await db.execute('SELECT COUNT(*) FROM job_postings')
            stats['total_jobs'] = (await cursor.fetchone())[0]
            
            # Analyzed jobs
            cursor = await db.execute('SELECT COUNT(*) FROM job_analysis')
            stats['analyzed_jobs'] = (await cursor.fetchone())[0]
            
            # Worth checking jobs
            cursor = await db.execute('SELECT COUNT(*) FROM job_analysis WHERE worth_checking = TRUE')
            stats['worth_checking'] = (await cursor.fetchone())[0]
            
            # Jobs in last 24 hours
            day_ago = datetime.now() - timedelta(hours=24)
            cursor = await db.execute('SELECT COUNT(*) FROM job_postings WHERE scraped_at > ?', (day_ago,))
            stats['jobs_last_24h'] = (await cursor.fetchone())[0]
            
            # Failed analysis count
            cursor = await db.execute('SELECT COUNT(*) FROM job_postings WHERE analysis_failed = TRUE')
            stats['failed_analysis'] = (await cursor.fetchone())[0]
            
            return stats