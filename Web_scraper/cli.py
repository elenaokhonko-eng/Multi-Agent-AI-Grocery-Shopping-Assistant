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
from dataclasses import asdict

from scrapers import GlowmarkScraper, KaprukaScraper, OnlineKadeScraper
from retrieval import ItemRetriever
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
  %(prog)s rice                              # Advanced retrieval (scraping + similarity)
  %(prog)s rice --mode scrape                # Fresh scraping only
  %(prog)s rice --mode search                # Similarity search only
  %(prog)s rice -s glowmark                  # Retrieve from specific site
  %(prog)s rice --parallel                   # Use parallel execution
  %(prog)s rice --max-results 5              # Limit number of results
  %(prog)s rice --min-similarity 0.5         # Higher similarity threshold
  %(prog)s rice --output results.json        # Save results to file
  %(prog)s rice --format table --verbose     # Table format with verbose logging
        """
    )
    
    parser.add_argument(
        "query",
        help="Search query (e.g., 'rice', 'vegetables')"
    )
    
    parser.add_argument(
        "--mode",
        choices=["scrape", "search", "retrieve"],
        default="retrieve",
        help="Operation mode: scrape (fresh only), search (similarity only), retrieve (combined)"
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
        "--min-similarity",
        type=float,
        default=0.3,
        help="Minimum similarity score for search results (default: 0.3)"
    )
    
    parser.add_argument(
        "--max-results",
        type=int,
        default=20,
        help="Maximum number of results to return (default: 20)"
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

def print_retrieval_summary(results: List[Any], summary: Any):
    """Print summary for retrieval results."""
    print(f"\n{'='*60}")
    print(f"RETRIEVAL RESULTS FOR: '{summary.query.upper()}'")
    print(f"{'='*60}")
    
    print(f"Mode: Advanced Retrieval")
    print(f"Total results: {summary.total_results}")
    print(f"Execution time: {summary.execution_time:.2f}s")
    
    if hasattr(summary, 'scraped_results') and hasattr(summary, 'similarity_results'):
        print(f"Scraped items: {summary.scraped_results}")
        print(f"Similar items: {summary.similarity_results}")
    
    if hasattr(summary, 'price_range') and summary.price_range:
        pr = summary.price_range
        print(f"Price range: {format_currency(pr['min'])} - {format_currency(pr['max'])}")
        print(f"Average price: {format_currency(pr['avg'])}")
    
    if hasattr(summary, 'best_match') and summary.best_match:
        bm = summary.best_match
        print(f"\nBest match: {bm.title}")
        print(f"  Price: {format_currency(bm.price_lkr)}")
        print(f"  Source: {bm.source} ({bm.website})")
    
    print(f"\n{'='*60}")
    print(f"Top {min(5, len(results))} results:")
    print(f"{'='*60}")
    
    for i, result in enumerate(results[:5], 1):
        if hasattr(result, 'title'):
            title = result.title
            price = result.price_lkr
            website = result.website
            source = result.source
            similarity = getattr(result, 'similarity_score', None)
        else:
            title = result.get('title', 'N/A')
            price = result.get('price_lkr', 0)
            website = result.get('website', 'N/A')
            source = result.get('source', 'N/A')
            similarity = result.get('similarity_score')
        
        print(f"{i}. {title}")
        print(f"   Price: {format_currency(price)}")
        print(f"   Source: {source} ({website})")
        if similarity:
            print(f"   Similarity: {similarity:.3f}")
        print()

def print_retrieval_table(results: List[Any], summary: Any):
    """Print results in table format for retrieval."""
    print(f"\nRetrieval Results for '{summary.query}'")
    print("-" * 90)
    print(f"{'#':<3} {'Title':<40} {'Price':<12} {'Source':<10} {'Website':<15} {'Similarity':<10}")
    print("-" * 90)
    
    for i, result in enumerate(results[:20], 1):
        if hasattr(result, 'title'):
            title = result.title[:37] + "..." if len(result.title) > 40 else result.title
            price = f"LKR {result.price_lkr:.0f}" if result.price_lkr else "N/A"
            source = result.source
            website = result.website[:12] + "..." if len(result.website) > 15 else result.website
            similarity = f"{result.similarity_score:.3f}" if getattr(result, 'similarity_score', None) else "N/A"
        else:
            title = (result.get('title', 'N/A')[:37] + "...") if len(result.get('title', '')) > 40 else result.get('title', 'N/A')
            price = f"LKR {result.get('price_lkr', 0):.0f}" if result.get('price_lkr') else "N/A"
            source = result.get('source', 'N/A')
            website = (result.get('website', 'N/A')[:12] + "...") if len(result.get('website', '')) > 15 else result.get('website', 'N/A')
            similarity = f"{result.get('similarity_score', 0):.3f}" if result.get('similarity_score') else "N/A"
        
        print(f"{i:<3} {title:<40} {price:<12} {source:<10} {website:<15} {similarity:<10}")
    
    print("-" * 90)
    print(f"Total: {summary.total_results} results in {summary.execution_time:.2f}s")
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
    
    print(f"Searching for '{args.query}' using {args.mode} mode...")
    if args.mode == "scrape":
        print(f"Scraping {len(scrapers_to_run)} site(s)")
    elif args.mode == "search":
        print("Using similarity search only")
    else:  # retrieve
        print(f"Using advanced retrieval (scraping + similarity)")
    
    if args.parallel and args.mode in ["scrape", "retrieve"]:
        print("Using parallel execution")
    
    try:
        # Run based on mode
        if args.mode == "scrape":
            # Traditional scraping only
            if args.parallel:
                results = asyncio.run(run_scrapers_parallel(scrapers_to_run, args.query, args.timeout))
            else:
                results = run_scrapers_sequential(scrapers_to_run, args.query)
            
            # Convert to consistent format
            formatted_results = []
            for site, result in results.items():
                if result.get("success"):
                    formatted_results.extend([{
                        "title": f"Item from {site}",  # Placeholder since we don't have individual items
                        "price_lkr": 0,
                        "website": site,
                        "source": "scraped",
                        "items_count": result.get("items_count", 0)
                    }])
            
            summary = type('Summary', (), {
                'query': args.query,
                'total_results': sum(r.get("items_count", 0) for r in results.values()),
                'execution_time': max(r.get("execution_time", 0) for r in results.values()),
                'price_range': None
            })()
            
        elif args.mode == "search":
            # Similarity search only
            retriever = ItemRetriever()
            try:
                search_results = retriever.search_similar_items(
                    args.query, 
                    top_k=args.max_results, 
                    min_similarity=args.min_similarity
                )
                
                formatted_results = search_results
                summary = type('Summary', (), {
                    'query': args.query,
                    'total_results': len(search_results),
                    'execution_time': 0,  # Quick search
                    'price_range': None
                })()
                
            finally:
                retriever.close()
                
        else:  # retrieve mode
            # Advanced retrieval combining scraping and similarity
            retriever = ItemRetriever()
            try:
                formatted_results, summary = retriever.retrieve_sync(
                    query=args.query,
                    max_results=args.max_results,
                    include_scraping=True,
                    include_similarity=True,
                    scrape_sites=site_names,
                    min_similarity=args.min_similarity
                )
            finally:
                retriever.close()
        
        # Output results based on format
        if args.format == "json":
            if args.mode == "scrape":
                output = {
                    "query": args.query,
                    "mode": args.mode,
                    "sites": site_names,
                    "results": results,
                    "total_items": summary.total_results
                }
            else:
                output = {
                    "query": args.query,
                    "mode": args.mode,
                    "results": [asdict(r) if hasattr(r, '__dict__') else r for r in formatted_results],
                    "summary": asdict(summary) if hasattr(summary, '__dict__') else summary.__dict__,
                    "total_results": summary.total_results
                }
            print(json.dumps(output, indent=2, default=str))
            
        elif args.format == "table":
            if args.mode == "scrape":
                print_table(results, args.query)
            else:
                print_retrieval_table(formatted_results, summary)
        else:  # summary
            if args.mode == "scrape":
                print_summary(results, args.query)
            else:
                print_retrieval_summary(formatted_results, summary)
        
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
        if args.mode == "scrape":
            successful_sites = sum(1 for r in results.values() if r.get("success"))
            total_sites = len(scrapers_to_run)
            if successful_sites == 0:
                print("No sites scraped successfully")
                sys.exit(1)
            elif successful_sites < total_sites:
                print(f"Warning: Only {successful_sites}/{total_sites} sites succeeded")
                sys.exit(2)
        else:
            # For search and retrieve modes
            if summary.total_results == 0:
                print("No results found")
                sys.exit(1)
            elif summary.total_results < 5:  # Arbitrary threshold for "few results"
                print(f"Warning: Only {summary.total_results} results found")
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
