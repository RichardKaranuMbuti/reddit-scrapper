# app/utils.py
"""Utility functions for time parsing and data processing"""

import re
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def parse_reddit_time(time_str: str) -> Optional[datetime]:
    """
    Parse Reddit's relative time strings into datetime objects
    
    Examples:
    - "34 min. ago" -> datetime 34 minutes ago
    - "12 hr. ago" -> datetime 12 hours ago  
    - "6 days ago" -> datetime 6 days ago
    - "2 weeks ago" -> datetime 14 days ago
    - "3 months ago" -> datetime 90 days ago (approximate)
    - "1 year ago" -> datetime 365 days ago
    - "just now" -> current datetime
    """
    if not time_str or not isinstance(time_str, str):
        return None
    
    time_str = time_str.lower().strip()
    now = datetime.now()
    
    # Handle "just now" case
    if time_str in ["just now", "now"]:
        return now
    
    # Extract number and unit using regex
    # Matches patterns like: "34 min. ago", "12 hr. ago", "6 days ago"
    pattern = r'(\d+)\s*(min\.?|minute\.?|hr\.?|hour\.?|day\.?|week\.?|month\.?|year\.?)'
    match = re.search(pattern, time_str)
    
    if not match:
        logger.warning(f"Could not parse time string: '{time_str}'")
        return None
    
    try:
        number = int(match.group(1))
        unit = match.group(2)
        
        # Normalize unit variations
        if unit.startswith('min'):
            delta = timedelta(minutes=number)
        elif unit.startswith('hr') or unit.startswith('hour'):
            delta = timedelta(hours=number)
        elif unit.startswith('day'):
            delta = timedelta(days=number)
        elif unit.startswith('week'):
            delta = timedelta(weeks=number)
        elif unit.startswith('month'):
            # Approximate: 30 days per month
            delta = timedelta(days=number * 30)
        elif unit.startswith('year'):
            # Approximate: 365 days per year
            delta = timedelta(days=number * 365)
        else:
            logger.warning(f"Unknown time unit in: '{time_str}'")
            return None
        
        parsed_time = now - delta
        logger.debug(f"Parsed '{time_str}' -> {parsed_time}")
        return parsed_time
        
    except (ValueError, OverflowError) as e:
        logger.error(f"Error parsing time '{time_str}': {e}")
        return None


def calculate_time_priority(time_str: str) -> int:
    """
    Calculate priority score for sorting (higher = more recent)
    Returns minutes since epoch (negative for sorting newest first)
    """
    parsed_time = parse_reddit_time(time_str)
    if parsed_time:
        # Convert to minutes since epoch, but negative so newer items have higher values
        minutes_since_epoch = int(parsed_time.timestamp() / 60)
        return minutes_since_epoch
    else:
        # If we can't parse, give it very low priority
        return 0


def format_time_ago(time_str: str) -> str:
    """
    Format time string for consistent display
    """
    if not time_str:
        return "Unknown"
    
    parsed_time = parse_reddit_time(time_str)
    if not parsed_time:
        return time_str  # Return original if can't parse
    
    now = datetime.now()
    diff = now - parsed_time
    
    # Format as human-readable relative time
    if diff.total_seconds() < 60:
        return "Just now"
    elif diff.total_seconds() < 3600:  # Less than 1 hour
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} min{'s' if minutes != 1 else ''} ago"
    elif diff.total_seconds() < 86400:  # Less than 1 day
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hr{'s' if hours != 1 else ''} ago"
    elif diff.days < 7:  # Less than 1 week
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.days < 30:  # Less than 1 month
        weeks = diff.days // 7
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif diff.days < 365:  # Less than 1 year
        months = diff.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = diff.days // 365
        return f"{years} year{'s' if years != 1 else ''} ago"


def sort_jobs_by_recency(jobs: list, time_field: str = 'time_posted') -> list:
    """
    Sort jobs by recency using parsed time strings
    Most recent jobs first
    """
    def get_sort_key(job):
        time_str = job.get(time_field, '')
        priority = calculate_time_priority(time_str)
        return priority
    
    # Sort in descending order (most recent first)
    return sorted(jobs, key=get_sort_key, reverse=True)


# Test function to validate parsing
def test_time_parsing():
    """Test the time parsing function with various inputs"""
    test_cases = [
        "34 min. ago",
        "12 hr. ago", 
        "6 days ago",
        "2 weeks ago",
        "3 months ago",
        "1 year ago",
        "just now",
        "5 minutes ago",
        "24 hours ago",
        "invalid time string"
    ]
    
    print("Testing time parsing:")
    for test_case in test_cases:
        parsed = parse_reddit_time(test_case)
        priority = calculate_time_priority(test_case)
        formatted = format_time_ago(test_case)
        print(f"'{test_case}' -> {parsed} (priority: {priority}) -> '{formatted}'")


if __name__ == "__main__":
    # Run tests
    test_time_parsing()