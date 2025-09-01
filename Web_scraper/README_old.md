# En## Features

- **Multi-site scraping**: Supports Glowmark, Kapruka, and OnlineKade
- **Semantic similarity search**: Find relevant products using AI embeddings
- **Advanced item retrieval**: Combines fresh scraping with similarity search
- **Parallel execution**: Scrape multiple sites concurrently for faster results
- **Enhanced API**: RESTful Flask API with comprehensive endpoints
- **Command-line interface**: Full-featured CLI for batch operations
- **Robust error handling**: Retry logic, timeouts, and graceful failure handling
- **Data validation**: Clean and validate all extracted product data
- **Intelligent ranking**: Rank results by relevance, freshness, and price
- **Flexible output**: JSON, table, and summary formats
- **Configuration management**: Environment-based configuration
- **Comprehensive logging**: Structured logging with configurable levels
- **Database integration**: MongoDB with upsert operations to avoid duplicates
- **Caching system**: Intelligent caching for similarity search performancemerce Scraper

A refactored and enhanced version of the e-commerce scraper with improved architecture, better error handling, and additional features.

## Features

- **Multi-site scraping**: Supports Glowmark, Kapruka, and OnlineKade
- **Parallel execution**: Scrape multiple sites concurrently for faster results
- **Enhanced API**: RESTful Flask API with comprehensive endpoints
- **Command-line interface**: Full-featured CLI for batch operations
- **Robust error handling**: Retry logic, timeouts, and graceful failure handling
- **Data validation**: Clean and validate extracted product data
- **Flexible output**: JSON, table, and summary formats
- **Configuration management**: Environment-based configuration
- **Comprehensive logging**: Structured logging with configurable levels
- **Database integration**: MongoDB with upsert operations to avoid duplicates

## Project Structure

```
refactored/
├── scrapers/           # Scraper implementations
│   ├── base_scraper.py     # Base scraper class
│   ├── glowmark_scraper.py # Glowmark implementation
│   ├── kapruka_scraper.py  # Kapruka implementation
│   └── onlinekade_scraper.py # OnlineKade implementation
├── retrieval/          # Item retrieval and similarity search
│   ├── similarity_search.py   # Semantic search engine
│   └── item_retriever.py      # Advanced retrieval system
├── config/             # Configuration management
│   └── settings.py         # Settings and configuration
├── utils/              # Utility functions
│   └── helpers.py          # Helper functions
├── data/               # Data storage directory
├── app.py              # Flask web application
├── cli.py              # Command-line interface
├── requirements.txt    # Python dependencies
└── .env.example        # Environment variables template
```

## Installation

1. **Clone and navigate to the refactored directory**:
   ```bash
   cd /path/to/Tensor-Titans-SLAIC-2025/Item_scaper/refactored
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your actual API keys and settings
   ```

5. **Ensure MongoDB is running**:
   ```bash
   # Start MongoDB if not already running
   mongod
   ```

## Usage

### Command Line Interface

The CLI provides multiple operation modes for different use cases:

```bash
# Advanced retrieval (combines fresh scraping + similarity search)
python cli.py "rice"

# Fresh scraping only
python cli.py "vegetables" --mode scrape -s glowmark,kapruka

# Similarity search only (fast, uses existing data)
python cli.py "fruits" --mode search --min-similarity 0.5

# Advanced retrieval with custom parameters
python cli.py "tea" --mode retrieve --max-results 15 --parallel

# Save results to file with table format
python cli.py "sugar" -o results.json --format table

# High similarity threshold for precise matches
python cli.py "basmati rice" --mode search --min-similarity 0.7

# Verbose logging for debugging
python cli.py "milk" --verbose
```

### Web API

Start the Flask application:

```bash
python app.py
```

The API will be available at `http://localhost:5000` with the following endpoints:

#### Endpoints

- **GET /** - API documentation homepage
- **GET /health** - Health check and status
- **GET /sites** - List available scraper sites
- **GET /scrape** - Scrape all or selected sites
- **GET /scrape/{site}** - Scrape a specific site
- **GET /retrieve** - Advanced retrieval (scraping + similarity)
- **GET /search** - Semantic similarity search
- **POST /search/refresh** - Refresh similarity search index
- **GET /stats** - System statistics

#### API Examples

```bash
# Advanced retrieval (recommended)
curl "http://localhost:5000/retrieve?query=rice&max_results=10"

# Fresh scraping only
curl "http://localhost:5000/scrape?query=vegetables&sites=glowmark,kapruka"

# Similarity search only (fast)
curl "http://localhost:5000/search?query=fruits&top_k=5&min_similarity=0.4"

# Scrape single site
curl "http://localhost:5000/scrape/glowmark?query=tea"

# Refresh search index
curl -X POST "http://localhost:5000/search/refresh"

# Get system statistics
curl "http://localhost:5000/stats"

# Sequential execution
curl "http://localhost:5000/scrape?query=sugar&parallel=false"
```

### Direct Usage

You can also use the scrapers and retrieval system directly:

```python
# Traditional scraping
from scrapers import GlowmarkScraper
scraper = GlowmarkScraper()
result = scraper.scrape_sync("rice")
print(f"Found {result['items_count']} items")
scraper.close()

# Advanced retrieval (recommended)
from retrieval import ItemRetriever
retriever = ItemRetriever()
results, summary = retriever.retrieve_sync("rice", max_results=10)
print(f"Found {summary.total_results} items")
print(f"Best match: {summary.best_match.title if summary.best_match else 'None'}")
retriever.close()

# Similarity search only
from retrieval import SimilaritySearchEngine
engine = SimilaritySearchEngine()
engine.load_data()
results = engine.search("basmati rice", top_k=5, min_similarity=0.4)
for result in results:
    print(f"{result.title} (similarity: {result.similarity_score:.3f})")
engine.close()

# Asynchronous usage
import asyncio
async def search_items():
    retriever = ItemRetriever()
    try:
        results, summary = await retriever.retrieve("rice", max_results=15)
        return results
    finally:
        retriever.close()

results = asyncio.run(search_items())
```

## Configuration

The application can be configured using environment variables or by editing `config/settings.py`:

### Key Configuration Options

- **GROQ_API_KEY**: Your Groq API key for LLM processing
- **MONGO_URI**: MongoDB connection string
- **LOG_LEVEL**: Logging level (DEBUG, INFO, WARNING, ERROR)
- **MAX_MARKDOWN_LENGTH**: Maximum content length sent to LLM
- **REQUEST_DELAY**: Delay between requests for rate limiting
- **SAVE_RAW_MARKDOWN**: Whether to save raw scraped content
- **SAVE_JSON_OUTPUT**: Whether to save extracted JSON data

## Output Format

The scrapers return structured data in the following format:

```json
{
  "success": true,
  "items_count": 15,
  "url": "https://example.com/search?q=rice",
  "website": "Glowmark",
  "execution_time": 4.12,
  "database_stats": {
    "inserted": 10,
    "matched": 5,
    "modified": 0
  },
  "item_stats": {
    "count": 15,
    "price_stats": {
      "min": 120.0,
      "max": 850.0,
      "avg": 425.5,
      "median": 400.0
    }
  },
  "query": "rice"
}
```

## Database Schema

Items are stored in MongoDB with the following structure:

```json
{
  "_id": "ObjectId(...)",
  "title": "Basmati Rice 1kg",
  "price_LKR": 450.0,
  "currency": "LKR",
  "source_url": "https://example.com/search?q=rice",
  "source_domain": "example.com",
  "website": "Glowmark",
  "scraped_at": "2025-09-01T10:30:00.000Z",
  "last_updated": "2025-09-01T10:30:00.000Z",
  "created_at": "2025-09-01T10:30:00.000Z"
}
```

## Key Improvements

### Over Original Code

1. **DRY Principle**: Eliminated code duplication with base scraper class
2. **Error Handling**: Comprehensive error handling with retries and timeouts
3. **Rate Limiting**: Built-in rate limiting to be respectful to websites
4. **Data Validation**: Clean and validate all extracted data
5. **Logging**: Structured logging throughout the application
6. **Configuration**: Environment-based configuration management
7. **Testing**: Easier to test with modular design
8. **Documentation**: Comprehensive documentation and examples

### New Features

1. **Command-line interface**: Full-featured CLI with multiple output formats
2. **Parallel execution**: Scrape multiple sites concurrently
3. **Enhanced API**: RESTful API with comprehensive endpoints
4. **Data statistics**: Calculate price statistics and other metrics
5. **Raw data saving**: Option to save raw scraped content for debugging
6. **Health monitoring**: API health checks and status monitoring
7. **Flexible output**: Multiple output formats (JSON, table, summary)
8. **Backwards compatibility**: Legacy functions still work

## Troubleshooting

### Common Issues

1. **MongoDB Connection Error**:
   - Ensure MongoDB is running: `mongod`
   - Check MONGO_URI in configuration

2. **Groq API Errors**:
   - Verify your API key is correct
   - Check API rate limits and quotas

3. **Import Errors**:
   - Ensure you're in the refactored directory
   - Install all requirements: `pip install -r requirements.txt`

4. **Network Timeouts**:
   - Increase timeout values in configuration
   - Check internet connection and website availability

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
# CLI
python cli.py "query" --verbose

# API (set in environment)
export LOG_LEVEL=DEBUG
python app.py
```

## Performance Tips

1. **Use parallel execution** for multiple sites when possible
2. **Adjust rate limiting** based on website requirements
3. **Monitor MongoDB performance** for large datasets
4. **Use appropriate timeout values** for your network conditions
5. **Consider caching** for frequently requested queries

## Contributing

1. Follow the existing code structure and patterns
2. Add proper error handling and logging
3. Update documentation for new features
4. Test thoroughly before submitting changes

## License

This project is part of the Tensor Titans SLAIC 2025 submission.
