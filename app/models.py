# app/models.py
"""Pydantic models for data validation and API responses"""
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ExperienceLevel(str, Enum):
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    UNSPECIFIED = "unspecified"


class JobType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time" 
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"
    UNSPECIFIED = "unspecified"


class RedFlags(str, Enum):
    NO_COMPENSATION = "no_compensation_mentioned"
    VAGUE_DESCRIPTION = "vague_job_description"
    UNREALISTIC_REQUIREMENTS = "unrealistic_requirements"
    POSSIBLE_SCAM = "possible_scam"
    NOT_ACTUALLY_HIRING = "not_actually_hiring"
    MULTILEVEL_MARKETING = "multilevel_marketing"
    UNPAID_WORK = "unpaid_work"
    POOR_COMMUNICATION = "poor_communication"


class JobPostingAnalysis(BaseModel):
    """Schema for OpenAI job posting analysis response"""
    worth_checking: bool = Field(..., description="Whether this job is worth the user's time to check")
    confidence_score: float = Field(..., ge=0, le=100, description="Confidence score from 0-100")
    job_type: JobType = Field(default=JobType.UNSPECIFIED, description="Type of job posting")
    compensation_mentioned: bool = Field(..., description="Whether compensation/salary is mentioned")
    remote_friendly: bool = Field(..., description="Whether the job supports remote work")
    experience_level: ExperienceLevel = Field(default=ExperienceLevel.UNSPECIFIED, description="Required experience level")
    red_flags: List[RedFlags] = Field(default=[], description="List of potential red flags")
    key_highlights: List[str] = Field(default=[], max_items=5, description="Key positive highlights")
    recommendation: str = Field(..., max_length=500, description="Brief recommendation for the user")
    
    @validator('key_highlights')
    def validate_highlights(cls, v):
        return [highlight.strip()[:100] for highlight in v if highlight.strip()]
    
    @validator('recommendation')
    def validate_recommendation(cls, v):
        return v.strip()


class JobPosting(BaseModel):
    """Schema for scraped job posting data"""
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(default="", max_length=10000)
    time_posted: str = Field(default="")
    url: HttpUrl = Field(..., description="Unique URL for the job posting")
    subreddit: str = Field(..., min_length=1)
    scraped_at: datetime = Field(default_factory=datetime.now)
    
    @validator('title', 'subreddit')
    def clean_text_fields(cls, v):
        return v.strip()
    
    @validator('description')
    def clean_description(cls, v):
        return v.strip()[:10000]  # Truncate if too long


class AnalyzedJobPosting(JobPosting):
    """Schema for job posting with AI analysis"""
    ai_analysis: Optional[JobPostingAnalysis] = None
    analysis_attempts: int = Field(default=0, ge=0)
    last_analysis_attempt: Optional[datetime] = None
    analysis_failed: bool = Field(default=False)
    failure_reason: Optional[str] = None


# API Response Models
class JobResponse(BaseModel):
    """API response model for job data"""
    id: int
    title: str
    description: str
    time_posted: str
    url: str
    subreddit: str
    scraped_at: datetime
    worth_checking: Optional[bool] = None
    confidence_score: Optional[float] = None
    job_type: Optional[str] = None
    compensation_mentioned: Optional[bool] = None
    remote_friendly: Optional[bool] = None
    experience_level: Optional[str] = None
    red_flags: Optional[List[str]] = None
    key_highlights: Optional[List[str]] = None
    recommendation: Optional[str] = None
    analyzed_at: Optional[datetime] = None


class JobFilters(BaseModel):
    """Model for job filtering parameters"""
    hours_back: int = Field(default=24, ge=1, le=8760)  # 1 hour to 1 year
    worth_checking_only: bool = Field(default=False)
    min_confidence: float = Field(default=0, ge=0, le=100)
    remote_only: bool = Field(default=False)
    compensation_mentioned_only: bool = Field(default=False)
    experience_level: Optional[ExperienceLevel] = None
    job_type: Optional[JobType] = None
    search_terms: Optional[str] = None
    limit: Optional[int] = Field(default=50, le=500)
    offset: int = Field(default=0, ge=0)


class StatsResponse(BaseModel):
    """API response model for statistics"""
    total_jobs: int
    analyzed_jobs: int
    worth_checking: int
    jobs_last_24h: int
    failed_analysis: int
    analysis_rate: float
    worth_checking_rate: float


class ScraperStatus(BaseModel):
    """Model for scraper status"""
    is_running: bool
    last_run: Optional[datetime] = None
    jobs_scraped_last_run: Optional[int] = None
    next_scheduled_run: Optional[datetime] = None