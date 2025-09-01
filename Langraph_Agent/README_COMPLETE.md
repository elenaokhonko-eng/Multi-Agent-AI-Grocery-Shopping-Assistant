# Complete Langraph System with Logistics Agent

## 🚀 System Overview

This is a comprehensive **Langraph-based product search and recommendation system** that integrates:

1. **LLM-Powered Keyword Extraction** using Groq API
2. **Knowledge Graph Enhancement** for better product discovery
3. **Web Scraper Integration** for real-time product data
4. **Advanced Personalization** with user preference filtering
5. **Logistics Optimization** with delivery cost and time calculation
6. **Minimum Guarantee Logic** ensuring at least 1 item per keyword category

## 🏗️ Architecture

### Agent-Based Pipeline (5 Nodes)
```
User Query → Keyword Extraction → Data Acquisition → Personalization → Logistics Optimization → Output Formatting
```

### Core Agents
- **KeywordExtractionAgent**: Extracts keywords using LLM
- **DataAcquisitionAgent**: Retrieves products using Web_scraper + Knowledge Graph
- **PersonalizationAgent**: Filters based on user preferences with 5 tools
- **LogisticsAgent**: Optimizes delivery options with distance calculations
- **OutputFormattingAgent**: Formats final results with all summaries

## 🔧 Key Features

### 1. Knowledge Graph Integration
- **15 nodes** and **14 relations** for product enhancement
- Automatic keyword expansion (e.g., "rice" → "samba rice", "nadu rice", "basmati rice")
- Enhanced search results with semantic relationships

### 2. Advanced Personalization
- **Budget filtering** with cost tracking
- **Dietary preferences** (vegetarian, organic, gluten-free, etc.)
- **Brand preferences** with priority handling
- **Inventory management** to avoid duplicates
- **Loyalty program** integration for discounts

### 3. Logistics Optimization
- **27 store locations** across Sri Lanka with GPS coordinates
- **Distance calculation** using Haversine formula
- **Delivery cost optimization** with distance-based pricing
- **Time estimation** with traffic factors
- **Multi-store delivery** coordination

### 4. Minimum Guarantee System
- **Keyword-level processing** ensures categories aren't eliminated
- **Fallback mechanisms** maintain at least 1 item per keyword
- **Personalization-aware** filtering with category preservation

## 📁 Project Structure

```
Langraph_Agent/
├── main.py                           # Main orchestrator
├── agents/
│   ├── keyword_extraction_agent.py   # LLM keyword extraction
│   ├── data_acquisition_agent.py     # Product data retrieval
│   ├── personalization_agent.py      # User preference filtering
│   ├── logistics_agent.py            # Delivery optimization
│   └── output_formatting_agent.py    # Result formatting
├── core/
│   ├── config.py                     # Configuration settings
│   ├── state.py                      # Langraph state management
│   └── user_profile.py               # User profile system
├── data/
│   ├── store_locations.py            # Store location database
│   └── knowledge_graph.json          # Product knowledge graph
├── utils/
│   ├── location_utils.py             # Location parsing utilities
│   ├── profile_manager.py            # User profile management
│   └── query_manager.py              # Query processing utilities
└── tests/
    ├── test_complete_pipeline.py     # Comprehensive testing
    └── demo_logistics.py             # Simple demonstration
```

## 🛠️ Technologies Used

- **Langraph**: Graph-based workflow orchestration
- **Groq API**: LLM for keyword extraction and tool calling (llama-3.3-70b-versatile)
- **LangChain**: Tool decorator pattern for LLM function execution
- **MongoDB**: Product data storage (via Web_scraper)
- **Vector Search**: Similarity-based product matching
- **Mathematical Calculations**: Haversine formula for distance calculations

## 🎯 Usage Examples

### Basic Usage
```python
from main import ProductSearchOrchestrator

orchestrator = ProductSearchOrchestrator()
result = orchestrator.process_query("I need organic rice and coconut oil")
```

### With User Profile
```python
from core.user_profile import UserProfile, DietaryNeeds, BrandPreferences

profile = UserProfile(
    user_id="customer123",
    budget_limit_lkr=3000.0,
    location="Galle, Sri Lanka",
    dietary_needs=DietaryNeeds(organic_only=True, vegetarian=True),
    brand_preferences=BrandPreferences(preferred_brands=["Prima", "Anchor"])
)

orchestrator = ProductSearchOrchestrator(user_profile=profile)
result = orchestrator.process_query("I need rice, coconut oil, and tea")
```

## 📊 Performance Metrics

### Search Capacity
- **10 results per keyword** (increased from 3)
- **Knowledge Graph enhancement** expands search scope
- **Multi-store coverage** across Sri Lanka

### Personalization Accuracy
- **5 filtering tools** for comprehensive personalization
- **Minimum guarantee** prevents category elimination
- **Budget tracking** with remaining balance calculation

### Logistics Optimization
- **27 store locations** with GPS coordinates
- **Distance-based delivery** cost calculation
- **Time estimation** with traffic factors
- **Multi-store coordination** for optimal delivery

## 🧪 Testing

Run the complete test suite:
```bash
python test_complete_pipeline.py
```

Run the simple demo:
```bash
python demo_logistics.py
```

## 🔄 Workflow Steps

1. **User Input**: Natural language query (e.g., "I need organic rice and tea")
2. **Keyword Extraction**: LLM extracts relevant keywords
3. **Data Acquisition**: Web_scraper + Knowledge Graph retrieve products
4. **Personalization**: Filter based on user preferences (budget, diet, brands)
5. **Logistics Optimization**: Calculate delivery options and costs
6. **Output Formatting**: Present results with all summaries

## 📈 Key Improvements

### From Previous Versions
- ✅ **Increased retrieval capacity** from 3-5 to 10 items per keyword
- ✅ **Added Logistics Agent** with delivery optimization
- ✅ **Store location database** with 27 locations across Sri Lanka
- ✅ **Distance calculation tools** using mathematical formulas
- ✅ **Delivery cost optimization** with distance-based pricing
- ✅ **Enhanced location parsing** supporting coordinates and city names

### System Robustness
- ✅ **Minimum guarantee logic** ensures at least 1 item per keyword
- ✅ **Fallback mechanisms** prevent empty result categories
- ✅ **Error handling** throughout the pipeline
- ✅ **Comprehensive logging** for debugging

## 🎉 Success Metrics

### Pipeline Completion
- ✅ **All 5 agents** working successfully
- ✅ **Langraph integration** with proper state management
- ✅ **LLM tool calling** with JSON mode and function execution
- ✅ **Personalization filters** maintaining minimum guarantees
- ✅ **Logistics optimization** with real store data

### Real-World Readiness
- ✅ **Sri Lankan store locations** with actual coordinates
- ✅ **Distance-based delivery** pricing and time estimates
- ✅ **Multi-store coordination** for optimal logistics
- ✅ **User preference** handling with comprehensive profiles
- ✅ **Budget management** with cost tracking and limits

This system successfully demonstrates a complete **Langraph-based product search and recommendation pipeline** with advanced personalization and logistics optimization capabilities, ready for real-world deployment.
