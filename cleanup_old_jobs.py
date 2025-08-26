#!/usr/bin/env python3
# cleanup_old_jobs.py
"""Script to remove job postings older than specified retention period"""

import asyncio
import logging
import argparse
from datetime import datetime, timedelta
from database import JobDatabase
from config import JOB_RETENTION_DAYS, DATABASE_FILE

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def cleanup_old_jobs(retention_days: int = JOB_RETENTION_DAYS, db_path: str = DATABASE_FILE):
    """Remove job postings older than retention period"""
    try:
        db = JobDatabase(db_path)
        
        # Get stats before cleanup
        stats_before = await db.get_stats()
        logger.info(f"Database stats before cleanup:")
        logger.info(f"  Total jobs: {stats_before['total_jobs']}")
        logger.info(f"  Analyzed jobs: {stats_before['analyzed_jobs']}")
        logger.info(f"  Worth checking: {stats_before['worth_checking']}")
        
        # Perform cleanup
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        logger.info(f"Removing jobs older than {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        deleted_count = await db.cleanup_old_jobs(retention_days)
        
        # Get stats after cleanup
        stats_after = await db.get_stats()
        logger.info(f"Database stats after cleanup:")
        logger.info(f"  Total jobs: {stats_after['total_jobs']}")
        logger.info(f"  Analyzed jobs: {stats_after['analyzed_jobs']}")
        logger.info(f"  Worth checking: {stats_after['worth_checking']}")
        
        logger.info(f"Cleanup completed successfully. Removed {deleted_count} old job postings.")
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise


async def get_database_stats(db_path: str = DATABASE_FILE):
    """Display current database statistics"""
    try:
        db = JobDatabase(db_path)
        stats = await db.get_stats()
        
        print("\n" + "="*50)
        print("DATABASE STATISTICS")
        print("="*50)
        print(f"Total job postings: {stats['total_jobs']}")
        print(f"Analyzed jobs: {stats['analyzed_jobs']}")
        print(f"Worth checking: {stats['worth_checking']}")
        print(f"Jobs in last 24h: {stats['jobs_last_24h']}")
        print(f"Failed analyses: {stats['failed_analysis']}")
        
        if stats['total_jobs'] > 0:
            analysis_rate = (stats['analyzed_jobs'] / stats['total_jobs']) * 100
            worth_checking_rate = (stats['worth_checking'] / max(stats['analyzed_jobs'], 1)) * 100
            print(f"\nAnalysis rate: {analysis_rate:.1f}%")
            print(f"Worth checking rate: {worth_checking_rate:.1f}%")
        
        print("="*50)
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        raise


def main():
    """Main function with command line arguments"""
    parser = argparse.ArgumentParser(description='Cleanup old job postings from database')
    parser.add_argument(
        '--days', 
        type=int, 
        default=JOB_RETENTION_DAYS,
        help=f'Number of days to retain jobs (default: {JOB_RETENTION_DAYS})'
    )
    parser.add_argument(
        '--db-path', 
        type=str, 
        default=DATABASE_FILE,
        help=f'Path to database file (default: {DATABASE_FILE})'
    )
    parser.add_argument(
        '--stats-only', 
        action='store_true',
        help='Only show database statistics without cleanup'
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    
    args = parser.parse_args()
    
    if args.stats_only:
        asyncio.run(get_database_stats(args.db_path))
        return
    
    if args.dry_run:
        print(f"DRY RUN: Would remove jobs older than {args.days} days")
        # In a real implementation, you'd query without deleting
        # For now, just show the cutoff date
        cutoff_date = datetime.now() - timedelta(days=args.days)
        print(f"Cutoff date would be: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
        return
    
    # Confirm before cleanup unless it's the default retention period
    if args.days != JOB_RETENTION_DAYS:
        confirm = input(f"Are you sure you want to delete jobs older than {args.days} days? (y/N): ")
        if confirm.lower() != 'y':
            print("Cleanup cancelled.")
            return
    
    # Run cleanup
    deleted_count = asyncio.run(cleanup_old_jobs(args.days, args.db_path))
    print(f"\nCleanup completed: {deleted_count} jobs removed.")


if __name__ == "__main__":
    main()