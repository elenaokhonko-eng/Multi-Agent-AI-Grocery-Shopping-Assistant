# Enhanced E-commerce Scraper

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

The CLI provides a simple way to scrape one or multiple sites:

```bash
# Basic usage - search all sites
python cli.py "rice"

# Search specific sites
python cli.py "vegetables" -s glowmark,kapruka

# Parallel execution
python cli.py "fruits" --parallel

# Save results to file
python cli.py "tea" -o results.json

# Different output formats
python cli.py "sugar" --format table
python cli.py "oil" --format json

# Verbose logging
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

#### API Examples

```bash
# Scrape all sites
curl "http://localhost:5000/scrape?query=rice"

# Scrape specific sites
curl "http://localhost:5000/scrape?query=vegetables&sites=glowmark,kapruka"

# Scrape single site
curl "http://localhost:5000/scrape/glowmark?query=fruits"

# Parallel execution (default)
curl "http://localhost:5000/scrape?query=tea&parallel=true"

# Sequential execution
curl "http://localhost:5000/scrape?query=sugar&parallel=false"
```

### Direct Scraper Usage

You can also use the scrapers directly in your Python code:

```python
from scrapers import GlowmarkScraper, KaprukaScraper, OnlineKadeScraper

# Create scraper instance
scraper = GlowmarkScraper()

# Synchronous scraping
result = scraper.scrape_sync("rice")
print(f"Found {result['items_count']} items")

# Asynchronous scraping
import asyncio
result = asyncio.run(scraper.scrape("vegetables"))

# Clean up
scraper.close()
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
