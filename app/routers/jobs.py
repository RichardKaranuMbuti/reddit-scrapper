# app/routers/jobs.py
"""API endpoints for job-related operations"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime, timedelta
import json
import logging

from app.models import JobResponse, JobFilters, StatsResponse
from app.database import JobDatabase
from config import DATABASE_FILE

logger = logging.getLogger(__name__)
router = APIRouter()

# Dependency to get database instance
async def get_db():
    db = JobDatabase(DATABASE_FILE)
    return db

@router.get("/jobs", response_model=List[JobResponse])
async def get_jobs(
    hours_back: int = Query(24, ge=1, le=8760, description="Hours to look back"),
    worth_checking_only: bool = Query(False, description="Only return jobs worth checking"),
    min_confidence: float = Query(0, ge=0, le=100, description="Minimum confidence score"),
    remote_only: bool = Query(False, description="Only remote-friendly jobs"),
    compensation_mentioned_only: bool = Query(False, description="Only jobs mentioning compensation"),
    experience_level: str = Query("", description="Filter by experience level"),
    job_type: str = Query("", description="Filter by job type"),
    search_terms: str = Query("", description="Search terms (space-separated)"),
    limit: int = Query(50, le=1000, description="Maximum number of jobs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: JobDatabase = Depends(get_db)
):
    """Get filtered job listings"""
    try:
        logger.info(f"Getting jobs with filters: hours_back={hours_back}, worth_checking_only={worth_checking_only}")
        
        # Get jobs from database
        jobs_data = await db.get_analyzed_jobs(hours_back, worth_checking_only)
        logger.info(f"Retrieved {len(jobs_data)} jobs from database")
        
        # Apply additional filters
        filtered_jobs = []
        for job in jobs_data:
            # Confidence filter
            confidence_score = job.get('confidence_score', 0)
            if confidence_score < min_confidence:
                continue
            
            # Remote filter
            if remote_only and not job.get('remote_friendly', False):
                continue
            
            # Compensation filter
            if compensation_mentioned_only and not job.get('compensation_mentioned', False):
                continue
            
            # Experience level filter
            if experience_level and experience_level.strip():
                if job.get('experience_level') != experience_level:
                    continue
            
            # Job type filter
            if job_type and job_type.strip():
                if job.get('job_type') != job_type:
                    continue
            
            # Search terms filter
            if search_terms and search_terms.strip():
                search_terms_lower = [term.strip().lower() for term in search_terms.split() if term.strip()]
                if search_terms_lower:
                    searchable_text = f"{job.get('title', '')} {job.get('description', '')} {job.get('subreddit', '')}".lower()
                    if not any(term in searchable_text for term in search_terms_lower):
                        continue
            
            filtered_jobs.append(job)
        
        logger.info(f"After filtering: {len(filtered_jobs)} jobs remain")
        
        # Sort by recency using time priority (most recent first)
        filtered_jobs.sort(key=lambda x: x.get('time_priority', 0), reverse=True)
        
        # Apply pagination
        total_jobs = len(filtered_jobs)
        paginated_jobs = filtered_jobs[offset:offset + limit]
        
        # Convert to response format
        response_jobs = []
        for job in paginated_jobs:
            try:
                # Use formatted time for display
                display_time = job.get('formatted_time', job.get('time_posted', ''))
                
                # Handle potential missing fields gracefully
                job_response = JobResponse(
                    id=job.get('id', 0),
                    title=job.get('title', 'Unknown Title'),
                    description=job.get('description', ''),
                    time_posted=display_time,  # Use formatted time
                    url=job.get('url', ''),
                    subreddit=job.get('subreddit', ''),
                    scraped_at=job.get('scraped_at') or datetime.now(),
                    worth_checking=job.get('worth_checking'),
                    confidence_score=float(job.get('confidence_score', 0)),
                    job_type=job.get('job_type'),
                    compensation_mentioned=job.get('compensation_mentioned'),
                    remote_friendly=job.get('remote_friendly'),
                    experience_level=job.get('experience_level'),
                    red_flags=job.get('red_flags', []),
                    key_highlights=job.get('key_highlights', []),
                    recommendation=job.get('recommendation'),
                    analyzed_at=job.get('analyzed_at')
                )
                response_jobs.append(job_response)
            except Exception as e:
                logger.error(f"Error processing job {job.get('id', 'unknown')}: {e}")
                # Log the problematic job data for debugging
                logger.debug(f"Problematic job data: {job}")
                continue
        
        logger.info(f"Returning {len(response_jobs)} jobs")
        return response_jobs
        
    except Exception as e:
        logger.error(f"Error in get_jobs endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")

@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: JobDatabase = Depends(get_db)):
    """Get a specific job by ID"""
    try:
        # This would require a new method in database.py to get a single job
        # For now, we'll get recent jobs and filter
        jobs = await db.get_analyzed_jobs(hours_back=8760)  # Get from last year
        
        job = next((j for j in jobs if j['id'] == job_id), None)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobResponse(
            id=job['id'],
            title=job['title'],
            description=job['description'],
            time_posted=job['time_posted'],
            url=job['url'],
            subreddit=job['subreddit'],
            scraped_at=job['scraped_at'],
            worth_checking=job.get('worth_checking'),
            confidence_score=job.get('confidence_score'),
            job_type=job.get('job_type'),
            compensation_mentioned=job.get('compensation_mentioned'),
            remote_friendly=job.get('remote_friendly'),
            experience_level=job.get('experience_level'),
            red_flags=job.get('red_flags', []),
            key_highlights=job.get('key_highlights', []),
            recommendation=job.get('recommendation'),
            analyzed_at=job.get('analyzed_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching job: {str(e)}")

@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: JobDatabase = Depends(get_db)):
    """Get database statistics"""
    try:
        stats = await db.get_stats()
        
        # Calculate rates
        analysis_rate = 0
        worth_checking_rate = 0
        
        if stats['total_jobs'] > 0:
            analysis_rate = (stats['analyzed_jobs'] / stats['total_jobs']) * 100
        
        if stats['analyzed_jobs'] > 0:
            worth_checking_rate = (stats['worth_checking'] / stats['analyzed_jobs']) * 100
        
        return StatsResponse(
            total_jobs=stats['total_jobs'],
            analyzed_jobs=stats['analyzed_jobs'],
            worth_checking=stats['worth_checking'],
            jobs_last_24h=stats['jobs_last_24h'],
            failed_analysis=stats['failed_analysis'],
            analysis_rate=round(analysis_rate, 1),
            worth_checking_rate=round(worth_checking_rate, 1)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

@router.get("/jobs/export/csv")
async def export_jobs_csv(
    hours_back: int = Query(24, ge=1, le=8760),
    worth_checking_only: bool = Query(False),
    db: JobDatabase = Depends(get_db)
):
    """Export jobs as CSV"""
    from fastapi.responses import StreamingResponse
    import csv
    import io
    
    try:
        jobs = await db.get_analyzed_jobs(hours_back, worth_checking_only)
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'id', 'title', 'description', 'url', 'subreddit', 'time_posted',
            'scraped_at', 'worth_checking', 'confidence_score', 'job_type',
            'experience_level', 'remote_friendly', 'compensation_mentioned',
            'key_highlights', 'red_flags', 'recommendation', 'analyzed_at'
        ])
        
        writer.writeheader()
        for job in jobs:
            # Convert lists to strings for CSV
            job_copy = job.copy()
            job_copy['key_highlights'] = '; '.join(job.get('key_highlights', []))
            job_copy['red_flags'] = '; '.join(job.get('red_flags', []))
            writer.writerow(job_copy)
        
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=jobs_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting CSV: {str(e)}")

@router.get("/jobs/export/json")
async def export_jobs_json(
    hours_back: int = Query(24, ge=1, le=8760),
    worth_checking_only: bool = Query(False),
    db: JobDatabase = Depends(get_db)
):
    """Export jobs as JSON"""
    from fastapi.responses import StreamingResponse
    import json
    import io
    
    try:
        jobs = await db.get_analyzed_jobs(hours_back, worth_checking_only)
        
        # Convert datetime objects to strings
        for job in jobs:
            if isinstance(job.get('scraped_at'), datetime):
                job['scraped_at'] = job['scraped_at'].isoformat()
            if isinstance(job.get('analyzed_at'), datetime):
                job['analyzed_at'] = job['analyzed_at'].isoformat()
        
        json_content = json.dumps(jobs, indent=2, default=str)
        
        return StreamingResponse(
            io.BytesIO(json_content.encode()),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=jobs_{datetime.now().strftime('%Y%m%d_%H%M')}.json"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting JSON: {str(e)}")