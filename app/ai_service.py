# ai_service.py
"""OpenAI service for job posting analysis"""
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import random
from openai import AsyncOpenAI
from pydantic import ValidationError

from app.models import JobPostingAnalysis
from app.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from config import OPENAI_MODEL, MAX_RETRIES, RETRY_DELAY

logger = logging.getLogger(__name__)


class AIAnalysisService:
    """Service for analyzing job postings with OpenAI"""
    
    def __init__(self, api_key: str, model: str = OPENAI_MODEL):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.max_retries = MAX_RETRIES
        self.base_delay = RETRY_DELAY
        
    async def analyze_single_job(self, job_data: Dict[str, Any]) -> Tuple[bool, Optional[JobPostingAnalysis], Optional[str]]:
        """
        Analyze a single job posting
        Returns: (success, analysis_result, error_message)
        """
        for attempt in range(self.max_retries + 1):
            try:
                user_prompt = USER_PROMPT_TEMPLATE.format(
                    title=job_data.get('title', 'N/A'),
                    subreddit=job_data.get('subreddit', 'N/A'),
                    time_posted=job_data.get('time_posted', 'N/A'),
                    url=job_data.get('url', 'N/A'),
                    description=job_data.get('description', 'No description available')[:3000]  # Limit description length
                )
                
                completion = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=800,
                    response_format={"type": "json_object"}  # Force JSON response
                )
                
                response_content = completion.choices[0].message.content.strip()
                
                # Parse and validate JSON response
                try:
                    analysis_data = json.loads(response_content)
                    analysis = JobPostingAnalysis(**analysis_data)
                    
                    logger.debug(f"Successfully analyzed: {job_data.get('title', 'Unknown')[:50]}... - Worth checking: {analysis.worth_checking}")
                    return True, analysis, None
                    
                except json.JSONDecodeError as e:
                    error_msg = f"Invalid JSON response: {e}"
                    logger.warning(f"JSON decode error on attempt {attempt + 1}: {error_msg}")
                    
                except ValidationError as e:
                    error_msg = f"Validation error: {e}"
                    logger.warning(f"Validation error on attempt {attempt + 1}: {error_msg}")
                
                # If we get here, there was a parsing/validation error
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Retrying analysis in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    return False, None, f"Failed after {self.max_retries + 1} attempts: {error_msg}"
                    
            except Exception as e:
                error_msg = f"OpenAI API error: {e}"
                logger.error(f"Analysis error on attempt {attempt + 1}: {error_msg}")
                
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Retrying analysis in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    return False, None, error_msg
        
        return False, None, "Maximum retries exceeded"
    
    async def analyze_job_batch(self, jobs: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], bool, Optional[JobPostingAnalysis], Optional[str]]]:
        """
        Analyze a batch of jobs concurrently
        Returns: List of (job_data, success, analysis_result, error_message)
        """
        if not jobs:
            return []
        
        logger.info(f"Starting analysis of {len(jobs)} jobs...")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent requests
        
        async def analyze_with_semaphore(job_data):
            async with semaphore:
                success, analysis, error = await self.analyze_single_job(job_data)
                return job_data, success, analysis, error
        
        # Execute all analyses concurrently
        tasks = [analyze_with_semaphore(job) for job in jobs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions that occurred during batch processing
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                job_data = jobs[i]
                error_msg = f"Batch processing error: {result}"
                logger.error(f"Error processing job {i}: {error_msg}")
                final_results.append((job_data, False, None, error_msg))
            else:
                final_results.append(result)
        
        # Log batch results
        successful = sum(1 for _, success, _, _ in final_results if success)
        failed = len(final_results) - successful
        
        logger.info(f"Batch analysis complete: {successful} successful, {failed} failed")
        
        return final_results
    
    async def test_connection(self) -> bool:
        """Test OpenAI API connection"""
        try:
            test_job = {
                'title': 'Senior Python Developer [HIRING]',
                'description': 'We are looking for a senior Python developer to join our remote team.',
                'subreddit': 'PythonJobs',
                'time_posted': '2 hours ago',
                'url': 'https://reddit.com/test'
            }
            
            success, analysis, error = await self.analyze_single_job(test_job)
            if success:
                logger.info("OpenAI connection test successful")
                return True
            else:
                logger.error(f"OpenAI connection test failed: {error}")
                return False
                
        except Exception as e:
            logger.error(f"OpenAI connection test error: {e}")
            return False