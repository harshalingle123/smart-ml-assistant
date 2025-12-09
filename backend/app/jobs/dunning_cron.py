"""
Dunning Cron Job
Processes pending payment retries on a schedule

Run this script via:
1. Manual: python -m app.jobs.dunning_cron
2. Cron: */30 * * * * cd /path/to/backend && python -m app.jobs.dunning_cron
3. System scheduler (Windows Task Scheduler, systemd timer, etc.)

Recommended Schedule: Every 30 minutes or hourly
"""
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.mongodb import mongodb
from app.services.dunning_service import dunning_service
from app.services.subscription_service import subscription_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('dunning_cron.log')
    ]
)
logger = logging.getLogger(__name__)


async def process_dunning():
    """Process all pending dunning attempts"""
    logger.info("=" * 60)
    logger.info("Starting dunning cron job")
    logger.info(f"Timestamp: {datetime.utcnow()}")
    logger.info("=" * 60)

    try:
        # Connect to MongoDB
        await mongodb.connect_to_mongo()
        logger.info("Connected to MongoDB")

        # Process pending dunning attempts
        logger.info("Processing pending dunning attempts...")
        dunning_result = await dunning_service.process_pending_retries()

        logger.info(f"Dunning processing completed:")
        logger.info(f"  - Processed: {dunning_result['processed']}")
        logger.info(f"  - Succeeded: {dunning_result['succeeded']}")
        logger.info(f"  - Failed: {dunning_result['failed']}")

        # Get dunning stats
        stats = await dunning_service.get_dunning_stats()
        logger.info(f"Overall dunning stats:")
        logger.info(f"  - Total attempts: {stats['total_attempts']}")
        logger.info(f"  - Pending: {stats['pending']}")
        logger.info(f"  - Success: {stats['success']}")
        logger.info(f"  - Recovery rate: {stats['recovery_rate']}%")

        logger.info("Dunning cron job completed successfully")
        return dunning_result

    except Exception as e:
        logger.error(f"Dunning cron job failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise

    finally:
        # Close MongoDB connection
        await mongodb.close_mongo_connection()
        logger.info("Disconnected from MongoDB")


async def check_expired_subscriptions():
    """Check and update expired subscriptions"""
    logger.info("Checking for expired subscriptions...")

    try:
        await subscription_service.check_expired_subscriptions()
        logger.info("Expired subscriptions check completed")

    except Exception as e:
        logger.error(f"Failed to check expired subscriptions: {str(e)}")


async def main():
    """Main cron job execution"""
    try:
        # Task 1: Process dunning
        await process_dunning()

        # Task 2: Check expired subscriptions
        await check_expired_subscriptions()

        logger.info("=" * 60)
        logger.info("All cron tasks completed successfully")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Cron job failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
