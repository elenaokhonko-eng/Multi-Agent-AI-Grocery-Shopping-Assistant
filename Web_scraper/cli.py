#!/usr/bin/env python3
"""
Command-line interface for the e-commerce scraper.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

from scrapers import GlowmarkScraper, KaprukaScraper, OnlineKadeScraper
from config.settings import Config
from utils.helpers import setup_logging, format_currency, calculate_stats

# Available scrapers
SCRAPERS = {
    "glowmark": GlowmarkScraper,
    "kapruka": KaprukaScraper,
    "onlinekade": OnlineKadeScraper
}

def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="E-commerce scraper for Sri Lankan websites",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s rice                          # Search for 'rice' on all sites
  %(prog)s rice -s glowmark              # Search only on Glowmark
  %(prog)s rice -s glowmark,kapruka      # Search on multiple sites
  %(prog)s rice --parallel               # Use parallel execution
  %(prog)s rice --output results.json    # Save results to file
  %(prog)s rice --verbose                # Enable verbose logging
        """
    )
    
    parser.add_argument(
        "query",
        help="Search query (e.g., 'rice', 'vegetables')"
    )
    
    parser.add_argument(
        "-s", "--sites",
        help=f"Comma-separated list of sites to scrape. Available: {', '.join(SCRAPERS.keys())}",
        default=",".join(SCRAPERS.keys())
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run scrapers in parallel (default: sequential)"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output file path (JSON format)"
    )
    
    parser.add_argument(
        "--format",
        choices=["json", "table", "summary"],
        default="summary",
        help="Output format (default: summary)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results to database"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout for each scraper in seconds (default: 60)"
    )
    
    return parser

def print_summary(results: Dict[str, Any], query: str):
    """Print a summary of scraping results."""
    print(f"\n{'='*60}")
    print(f"SCRAPING RESULTS FOR: '{query.upper()}'")
    print(f"{'='*60}")
    
    total_items = 0
    successful_sites = 0
    
    for site, result in results.items():
        print(f"\n{site.upper()}:")
        print("-" * 20)
        
        if result.get("success"):
            successful_sites += 1
            items_count = result.get("items_count", 0)
            total_items += items_count
            exec_time = result.get("execution_time", 0)
            
            print(f"✓ Success: {items_count} items found ({exec_time:.2f}s)")
            
            # Show price statistics if available
            stats = result.get("item_stats", {})
            if stats and stats.get("price_stats"):
                price_stats = stats["price_stats"]
                print(f"  Price range: {format_currency(price_stats['min'])} - {format_currency(price_stats['max'])}")
                print(f"  Average: {format_currency(price_stats['avg'])}")
        else:
            error = result.get("error", "Unknown error")
            print(f"✗ Failed: {error}")
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {total_items} total items from {successful_sites}/{len(results)} sites")
    print(f"{'='*60}\n")

def print_table(results: Dict[str, Any], query: str):
    """Print results in table format."""
    print(f"\nScraping Results for '{query}'")
    print("-" * 80)
    print(f"{'Site':<15} {'Status':<10} {'Items':<8} {'Time':<8} {'Min Price':<12} {'Max Price':<12}")
    print("-" * 80)
    
    for site, result in results.items():
        status = "✓ Success" if result.get("success") else "✗ Failed"
        items = result.get("items_count", 0)
        exec_time = f"{result.get('execution_time', 0):.1f}s"
        
        min_price = max_price = "N/A"
        stats = result.get("item_stats", {})
        if stats and stats.get("price_stats"):
            price_stats = stats["price_stats"]
            min_price = f"LKR {price_stats['min']:.0f}"
            max_price = f"LKR {price_stats['max']:.0f}"
        
        print(f"{site:<15} {status:<10} {items:<8} {exec_time:<8} {min_price:<12} {max_price:<12}")
    
    total_items = sum(r.get("items_count", 0) for r in results.values())
    print("-" * 80)
    print(f"Total: {total_items} items")
    print()

async def run_scrapers_parallel(scrapers_to_run: List[tuple], query: str, timeout: int) -> Dict[str, Any]:
    """Run scrapers in parallel."""
    async def run_single_scraper(name: str, scraper_class, query: str):
        scraper = scraper_class()
        try:
            result = await asyncio.wait_for(scraper.scrape(query), timeout=timeout)
            return name, result
        except asyncio.TimeoutError:
            return name, {"success": False, "error": f"Timeout after {timeout}s", "items_count": 0}
        except Exception as e:
            return name, {"success": False, "error": str(e), "items_count": 0}
        finally:
            scraper.close()
    
    tasks = [run_single_scraper(name, scraper_class, query) for name, scraper_class in scrapers_to_run]
    
    results = {}
    for task in asyncio.as_completed(tasks):
        name, result = await task
        results[name] = result
    
    return results

def run_scrapers_sequential(scrapers_to_run: List[tuple], query: str) -> Dict[str, Any]:
    """Run scrapers sequentially."""
    results = {}
    
    for name, scraper_class in scrapers_to_run:
        print(f"Scraping {name}...", end=" ", flush=True)
        scraper = scraper_class()
        try:
            result = scraper.scrape_sync(query)
            results[name] = result
            status = "✓" if result.get("success") else "✗"
            items = result.get("items_count", 0)
            print(f"{status} ({items} items)")
        except Exception as e:
            results[name] = {"success": False, "error": str(e), "items_count": 0}
            print(f"✗ Error: {e}")
        finally:
            scraper.close()
    
    return results

def main():
    """Main CLI function."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "WARNING"  # Reduce noise unless verbose
    logger = setup_logging(log_level)
    
    # Parse sites
    site_names = [s.strip().lower() for s in args.sites.split(",")]
    invalid_sites = [s for s in site_names if s not in SCRAPERS]
    
    if invalid_sites:
        print(f"Error: Unknown sites: {invalid_sites}")
        print(f"Available sites: {', '.join(SCRAPERS.keys())}")
        sys.exit(1)
    
    scrapers_to_run = [(name, SCRAPERS[name]) for name in site_names]
    
    print(f"Searching for '{args.query}' on {len(scrapers_to_run)} site(s)...")
    if args.parallel:
        print("Using parallel execution")
    
    try:
        # Run scrapers
        if args.parallel:
            results = asyncio.run(run_scrapers_parallel(scrapers_to_run, args.query, args.timeout))
        else:
            results = run_scrapers_sequential(scrapers_to_run, args.query)
        
        # Output results
        if args.format == "json":
            output = {
                "query": args.query,
                "sites": site_names,
                "results": results,
                "total_items": sum(r.get("items_count", 0) for r in results.values())
            }
            print(json.dumps(output, indent=2, default=str))
        elif args.format == "table":
            print_table(results, args.query)
        else:  # summary
            print_summary(results, args.query)
        
        # Save to file if requested
        if args.output:
            output_data = {
                "query": args.query,
                "sites": site_names,
                "parallel": args.parallel,
                "results": results,
                "total_items": sum(r.get("items_count", 0) for r in results.values()),
                "timestamp": asyncio.get_event_loop().time()
            }
            
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, "w") as f:
                json.dump(output_data, f, indent=2, default=str)
            print(f"Results saved to {args.output}")
        
        # Exit with appropriate code
        successful_sites = sum(1 for r in results.values() if r.get("success"))
        if successful_sites == 0:
            print("No sites scraped successfully")
            sys.exit(1)
        elif successful_sites < len(scrapers_to_run):
            print(f"Warning: Only {successful_sites}/{len(scrapers_to_run)} sites succeeded")
            sys.exit(2)
        
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
