"""
Automated query executor that processes saved search queries continuously.
"""

import asyncio
import signal
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from utils.query_manager import QueryManager, SavedQuery
from retrieval.item_retriever import ItemRetriever
from config.settings import Config
from utils.helpers import setup_logging

class QueryExecutor:
    """Automated executor that processes saved search queries continuously."""
    
    def __init__(
        self, 
        interval_seconds: int = 300,  # 5 minutes default
        batch_size: int = 10,
        max_runtime_hours: Optional[int] = None
    ):
        """
        Initialize the query executor.
        
        Args:
            interval_seconds: Time between query processing cycles
            batch_size: Number of queries to process in each batch
            max_runtime_hours: Maximum runtime before auto-shutdown (None for indefinite)
        """
        self.logger = setup_logging(Config.LOG_LEVEL, Config.LOG_FILE)
        self.interval_seconds = interval_seconds
        self.batch_size = batch_size
        self.max_runtime_hours = max_runtime_hours
        
        # Initialize components
        self.query_manager = QueryManager()
        self.item_retriever = ItemRetriever()
        
        # State tracking
        self.is_running = False
        self.start_time = None
        self.cycles_completed = 0
        self.queries_processed = 0
        self.successful_queries = 0
        self.failed_queries = 0
        
        # Graceful shutdown handling
        self._shutdown_requested = False
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info(
            f"QueryExecutor initialized: {interval_seconds}s interval, "
            f"batch size {batch_size}, max runtime {max_runtime_hours}h"
        )

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self._shutdown_requested = True

    def _should_shutdown(self) -> bool:
        """Check if executor should shutdown."""
        if self._shutdown_requested:
            return True
        
        if self.max_runtime_hours and self.start_time:
            runtime_hours = (time.time() - self.start_time) / 3600
            if runtime_hours >= self.max_runtime_hours:
                self.logger.info(f"Max runtime ({self.max_runtime_hours}h) reached")
                return True
        
        return False

    async def _process_query(self, query: SavedQuery) -> Dict[str, Any]:
        """Process a single query and return results."""
        start_time = time.time()
        
        try:
            self.logger.info(f"Processing query: '{query.query}'")
            
            # Use the item retriever to get results
            results, summary = await self.item_retriever.retrieve(
                query=query.query,
                max_results=20,
                include_scraping=True,
                include_similarity=True,
                min_similarity=0.3
            )
            
            execution_time = time.time() - start_time
            items_found = len(results)
            
            # Mark query as processed
            self.query_manager.mark_query_processed(
                query.query, 
                success=summary.total_results > 0,
                items_found=items_found
            )
            
            self.logger.info(
                f"Query '{query.query}' completed: {items_found} items "
                f"in {execution_time:.2f}s"
            )
            
            return {
                "query": query.query,
                "success": True,
                "items_found": items_found,
                "execution_time": execution_time,
                "scraped_items": summary.scraped_results,
                "similar_items": summary.similarity_results
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Error processing query '{query.query}': {e}")
            
            # Mark as failed
            self.query_manager.mark_query_processed(
                query.query, 
                success=False,
                items_found=0
            )
            
            return {
                "query": query.query,
                "success": False,
                "error": str(e),
                "execution_time": execution_time
            }

    async def _process_query_batch(self, queries: List[SavedQuery]) -> List[Dict[str, Any]]:
        """Process a batch of queries with some parallelization."""
        results = []
        
        # Process queries with a small delay to avoid overwhelming sites
        for i, query in enumerate(queries):
            if self._should_shutdown():
                break
            
            result = await self._process_query(query)
            results.append(result)
            
            if result["success"]:
                self.successful_queries += 1
            else:
                self.failed_queries += 1
            
            self.queries_processed += 1
            
            # Add delay between queries to be respectful
            if i < len(queries) - 1:  # Don't delay after the last query
                delay = random.uniform(2, 5)  # Random delay 2-5 seconds
                self.logger.debug(f"Waiting {delay:.1f}s before next query...")
                await asyncio.sleep(delay)
        
        return results

    async def _run_cycle(self) -> Dict[str, Any]:
        """Run one complete processing cycle."""
        cycle_start = time.time()
        
        try:
            # Get pending queries
            pending_queries = self.query_manager.get_pending_queries(self.batch_size)
            
            if not pending_queries:
                self.logger.info("No pending queries found, waiting for next cycle...")
                return {
                    "queries_processed": 0,
                    "execution_time": time.time() - cycle_start,
                    "status": "no_queries"
                }
            
            self.logger.info(f"Processing {len(pending_queries)} queries in this cycle")
            
            # Process the batch
            batch_results = await self._process_query_batch(pending_queries)
            
            # Calculate cycle statistics
            successful_in_cycle = sum(1 for r in batch_results if r["success"])
            total_items_found = sum(r.get("items_found", 0) for r in batch_results)
            
            cycle_time = time.time() - cycle_start
            
            self.logger.info(
                f"Cycle completed: {successful_in_cycle}/{len(batch_results)} successful, "
                f"{total_items_found} total items found in {cycle_time:.2f}s"
            )
            
            return {
                "queries_processed": len(batch_results),
                "successful_queries": successful_in_cycle,
                "failed_queries": len(batch_results) - successful_in_cycle,
                "total_items_found": total_items_found,
                "execution_time": cycle_time,
                "status": "completed",
                "results": batch_results
            }
            
        except Exception as e:
            cycle_time = time.time() - cycle_start
            self.logger.error(f"Error in processing cycle: {e}")
            
            return {
                "queries_processed": 0,
                "execution_time": cycle_time,
                "status": "error",
                "error": str(e)
            }

    async def run(self):
        """Main execution loop."""
        self.is_running = True
        self.start_time = time.time()
        
        self.logger.info("Starting QueryExecutor main loop...")
        
        try:
            while not self._should_shutdown():
                cycle_start = time.time()
                
                # Run processing cycle
                cycle_result = await self._run_cycle()
                self.cycles_completed += 1
                
                # Periodic maintenance
                if self.cycles_completed % 10 == 0:  # Every 10 cycles
                    self.logger.info("Running periodic maintenance...")
                    self.query_manager.deactivate_old_queries(days_old=30)
                    
                    # Refresh similarity search index periodically
                    try:
                        self.item_retriever.refresh_similarity_index()
                        self.logger.info("Similarity search index refreshed")
                    except Exception as e:
                        self.logger.warning(f"Failed to refresh similarity index: {e}")
                
                # Calculate sleep time
                cycle_duration = time.time() - cycle_start
                sleep_time = max(0, self.interval_seconds - cycle_duration)
                
                if sleep_time > 0:
                    self.logger.debug(f"Sleeping for {sleep_time:.1f}s until next cycle...")
                    await asyncio.sleep(sleep_time)
                else:
                    self.logger.warning(
                        f"Cycle took {cycle_duration:.1f}s, longer than interval "
                        f"({self.interval_seconds}s)"
                    )
        
        except Exception as e:
            self.logger.error(f"Fatal error in executor main loop: {e}")
            raise
        
        finally:
            self.is_running = False
            self.logger.info("QueryExecutor stopped")

    def get_stats(self) -> Dict[str, Any]:
        """Get executor statistics."""
        runtime = (time.time() - self.start_time) if self.start_time else 0
        
        return {
            "is_running": self.is_running,
            "runtime_seconds": runtime,
            "runtime_hours": runtime / 3600,
            "cycles_completed": self.cycles_completed,
            "queries_processed": self.queries_processed,
            "successful_queries": self.successful_queries,
            "failed_queries": self.failed_queries,
            "success_rate": (
                self.successful_queries / self.queries_processed 
                if self.queries_processed > 0 else 0
            ),
            "config": {
                "interval_seconds": self.interval_seconds,
                "batch_size": self.batch_size,
                "max_runtime_hours": self.max_runtime_hours
            },
            "query_manager_stats": self.query_manager.get_query_stats()
        }

    def stop(self):
        """Request graceful shutdown."""
        self._shutdown_requested = True
        self.logger.info("Shutdown requested")

    def close(self):
        """Clean up resources."""
        self.stop()
        
        try:
            self.query_manager.close()
        except Exception as e:
            self.logger.error(f"Error closing query manager: {e}")
        
        try:
            self.item_retriever.close()
        except Exception as e:
            self.logger.error(f"Error closing item retriever: {e}")
        
        self.logger.info("QueryExecutor resources cleaned up")

def run_executor_cli():
    """CLI function to run the executor."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the automated query executor")
    parser.add_argument("--interval", type=int, default=300, help="Interval between cycles (seconds)")
    parser.add_argument("--batch-size", type=int, default=10, help="Queries per batch")
    parser.add_argument("--max-hours", type=int, help="Maximum runtime in hours")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging level
    if args.verbose:
        import logging
        logging.getLogger("scraper").setLevel(logging.DEBUG)
    
    # Create and run executor
    executor = QueryExecutor(
        interval_seconds=args.interval,
        batch_size=args.batch_size,
        max_runtime_hours=args.max_hours
    )
    
    try:
        print(f"Starting query executor...")
        print(f"Interval: {args.interval}s, Batch size: {args.batch_size}")
        if args.max_hours:
            print(f"Max runtime: {args.max_hours} hours")
        print("Press Ctrl+C to stop gracefully")
        
        asyncio.run(executor.run())
        
        # Print final stats
        stats = executor.get_stats()
        print(f"\nFinal statistics:")
        print(f"Runtime: {stats['runtime_hours']:.2f} hours")
        print(f"Cycles: {stats['cycles_completed']}")
        print(f"Queries processed: {stats['queries_processed']}")
        print(f"Success rate: {stats['success_rate']:.1%}")
        
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        executor.close()

if __name__ == "__main__":
    run_executor_cli()
