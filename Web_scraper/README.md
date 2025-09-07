# Enhanced E-commerce Scraper with AI-Powered Retrieval and Query Management

A sophisticated web scraping system with semantic search capabilities and automated query management for e-commerce websites.

## 🌟 Features

### Core Functionality
- **Multi-site Scraping**: Concurrent scraping across multiple e-commerce platforms
- **AI-Powered Search**: FAISS-based semantic similarity search using sentence transformers
- **Intelligent Retrieval**: Combines fresh scraping with similarity search for optimal results
- **Query Management**: Automated query saving with similarity checking to prevent duplicates
- **Automated Processing**: Background executor that cycles through saved queries

### Supported Platforms
- Glowmark.lk
- Kapruka.com  
- OnlineKade.lk

### Technical Stack
- **Web Framework**: Flask with CORS support
- **Database**: MongoDB for data storage
- **AI/ML**: FAISS + sentence-transformers for semantic search
- **Scraping**: crawl4ai with LLM processing via Groq API
- **Concurrency**: asyncio and threading for parallel execution

## Project Structure

```
Web_scraper/
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

## 📋 Requirements

### System Requirements
- Python 3.8+
- MongoDB server
- Internet connection for scraping and AI processing

### API Keys
- Groq API key

## 🚀 Installation

1. **Clone and navigate to the project**
   ```bash
   cd Item_scaper/refactored
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp config/settings.py.example config/settings.py
   # Edit settings.py with your configuration
   ```

4. **Set up MongoDB**
   - Install and start MongoDB
   - Create database: `tensor_titans_scraper`

## ⚙️ Configuration

Edit `config/settings.py`:

```python
class Config:
    # Database configuration
    MONGODB_URI = "mongodb://localhost:27017"
    DATABASE_NAME = "ecommerce_db"
    
    # API configuration
    GROQ_API_KEY = "your_groq_api_key_here"
    
    # Search configuration
    SIMILARITY_THRESHOLD = 0.8  # For duplicate query detection
    
    # Logging
    LOG_LEVEL = "INFO"
```

## 🎯 Usage

### 1. Start the Flask API Server

```bash
python app.py
```

The API will be available at `http://localhost:5000`

### 2. Start the Query Executor (Optional)

For automated query processing:

```bash
python start_query_executor.py
```

### 3. API Endpoints

#### Core Scraping Endpoints

**Health Check**
```bash
GET /health
```

**Scrape Single Site**
```bash
GET /scrape/glowmark?query=laptop
```

**Scrape Multiple Sites**
```bash
GET /scrape?query=smartphone&sites=glowmark,kapruka&parallel=true
```

#### Advanced Retrieval Endpoints

**Intelligent Item Retrieval** (Recommended)
```bash
GET /retrieve?query=gaming%20laptop&max_results=10&include_scraping=true&include_similarity=true
```

**Similarity Search Only**
```bash
GET /search?query=bluetooth%20headphones&top_k=10&min_similarity=0.3
```

**Refresh Search Index**
```bash
POST /search/refresh
```

#### Query Management Endpoints

**Get Query Statistics**
```bash
GET /query-stats
```

**List Saved Queries**
```bash
GET /queries?status=pending&limit=20
```

**Update Query Status**
```bash
PUT /query/<query_id>/status
Content-Type: application/json
{
    "status": "processed"
}
```

**System Statistics**
```bash
GET /stats
```

### 4. Command Line Interface

```bash
# Single site scraping
python cli.py scrape --site glowmark --query "laptop" --output results.json

# Multi-site scraping
python cli.py scrape-all --query "smartphone" --parallel --output results.json

# Similarity search
python cli.py search --query "gaming mouse" --top-k 10 --output results.json

# Advanced retrieval
python cli.py retrieve --query "bluetooth speakers" --max-results 15 --output results.json

# Refresh search index
python cli.py refresh-index
```

## 🧪 Testing

### Run Comprehensive Tests
```bash
python test_query_system.py
```

### Test Individual Components
```bash
# Test migration (one-time)
python test_migration.py

# Test specific functionality
python -c "from utils.query_manager import QueryManager; qm = QueryManager(); print('✅ Query Manager OK')"
python -c "from retrieval import ItemRetriever; ir = ItemRetriever(); print('✅ Item Retriever OK')"
```

## 🔧 Query Management System

### How It Works

1. **Automatic Query Saving**: All search queries are automatically saved with similarity checking
2. **Duplicate Prevention**: Uses semantic similarity to avoid saving duplicate queries
3. **Background Processing**: Query executor runs saved queries periodically to keep data fresh
4. **Status Tracking**: Queries have statuses (pending, processing, processed, failed)

### Query Similarity Checking

The system uses sentence transformers to check if a new query is similar to existing ones:
- Similarity threshold: 0.8 (configurable)
- Model: "all-MiniLM-L6-v2"
- Prevents near-duplicate queries from being saved

### Automated Query Execution

The query executor:
- Processes queries in batches
- Configurable execution interval
- Graceful shutdown handling
- Detailed statistics and logging

## 📊 Data Structure

### Scraped Items
```json
{
    "title": "Gaming Laptop",
    "price_lkr": 150000,
    "currency": "LKR", 
    "source": "fresh_scrape",
    "website": "glowmark",
    "collection": "glowmark_items",
    "source_url": "https://...",
    "item_id": "unique_id",
    "timestamp": 1234567890
}
```

### Saved Queries
```json
{
    "_id": "query_id",
    "query_text": "gaming laptop",
    "query_type": "retrieve",
    "embedding": [0.1, 0.2, ...],
    "status": "pending",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "execution_count": 0,
    "last_executed": null
}
```

## 🔍 Search Strategies

### 1. Fresh Scraping Only
- Real-time data from websites
- Slower but most current results
- Use: `/scrape` endpoints

### 2. Similarity Search Only  
- Fast searches through existing data
- Uses semantic understanding
- Use: `/search` endpoint

### 3. Intelligent Retrieval (Recommended)
- Combines both approaches
- Balances speed and freshness
- Intelligent result ranking and deduplication
- Use: `/retrieve` endpoint

## 📈 Performance Features

- **Parallel Scraping**: Multiple sites scraped concurrently
- **Caching**: FAISS index caching for faster similarity searches
- **Rate Limiting**: Respectful scraping with delays
- **Error Handling**: Comprehensive error recovery
- **Logging**: Detailed logging for monitoring and debugging

## 🛠️ Troubleshooting

### Common Issues

**MongoDB Connection Error**
```bash
# Check MongoDB is running
systemctl status mongod  # Linux
brew services list | grep mongodb  # macOS
```

**Import Errors**
```bash
# Verify installation
python -c "import sentence_transformers; print('✅ OK')"
python -c "import faiss; print('✅ OK')"
```

**API Connection Issues**
```bash
# Test API health
curl http://localhost:5000/health
```

**Query Executor Not Processing**
```bash
# Check logs
tail -f query_executor.log
tail -f data/scraper.log
```

### Performance Optimization

1. **Increase batch size** for query executor (more concurrent processing)
2. **Adjust similarity threshold** (higher = fewer duplicate queries)
3. **Configure MongoDB indexes** for better query performance
4. **Use parallel scraping** for faster multi-site operations

## 📝 Logging

- **Application logs**: `data/scraper.log`
- **Query executor logs**: `query_executor.log`
- **Log levels**: DEBUG, INFO, WARNING, ERROR
- **Configurable** via `config/settings.py`
