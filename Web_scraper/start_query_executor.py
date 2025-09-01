#!/usr/bin/env python3
"""
Start the query executor as a background service.
"""

import asyncio
import signal
import sys
import logging
from utils.query_executor import QueryExecutor
from config.settings import Config

def setup_logging():
    """Setup logging for the query executor service."""
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('query_executor.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

async def main():
    """Main function to run the query executor."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Query Executor Service...")
    
    executor = QueryExecutor()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}. Shutting down gracefully...")
        executor.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await executor.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down...")
    except Exception as e:
        logger.error(f"Error in query executor: {e}")
    finally:
        logger.info("Query executor stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Failed to start query executor: {e}")
        sys.exit(1)
