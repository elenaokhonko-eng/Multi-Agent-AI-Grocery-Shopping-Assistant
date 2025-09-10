#!/usr/bin/env python3
"""
Simple MongoDB connection test without semantic search dependencies
"""

print("🔍 Testing MongoDB connection...")

# Test basic MongoDB connection
try:
    from pymongo import MongoClient
    
    print("✅ PyMongo imported successfully")
    
    # Try to connect
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
    
    # Test connection
    server_info = client.server_info()
    print(f"✅ MongoDB connected: {server_info['version']}")
    
    # Test database access
    db = client["ecommerce_db"]
    collections = db.list_collection_names()
    print(f"✅ Database accessed. Collections: {collections}")
    
    # Test querying each collection
    total_products = 0
    for collection_name in ["Glowmark", "Kapruka", "Lassana_Flora", "OnlineKade"]:
        if collection_name in collections:
            collection = db[collection_name]
            count = collection.count_documents({})
            print(f"✅ {collection_name}: {count} documents")
            total_products += count
            
            # Show a sample document
            sample = collection.find_one({}, {"_id": 0})
            if sample:
                print(f"   Sample: {sample.get('name', sample.get('title', 'No name'))}")
        else:
            print(f"❌ {collection_name}: Not found")
    
    print(f"\n🎯 Total products in database: {total_products}")
    
    # Test simple text search
    print("\n🔍 Testing simple text search for 'rice'...")
    glowmark = db["Glowmark"]
    rice_products = list(glowmark.find(
        {"$or": [
            {"name": {"$regex": "rice", "$options": "i"}},
            {"title": {"$regex": "rice", "$options": "i"}},
            {"description": {"$regex": "rice", "$options": "i"}}
        ]},
        {"_id": 0}
    ).limit(3))
    
    if rice_products:
        print(f"✅ Found {len(rice_products)} rice products:")
        for product in rice_products:
            name = product.get('name', product.get('title', 'No name'))
            price = product.get('price', 'No price')
            print(f"   - {name} ({price})")
    else:
        print("❌ No rice products found")
        
    client.close()
    print("\n✅ MongoDB test completed successfully!")
    
except ImportError as e:
    print(f"❌ PyMongo not available: {e}")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    print("   Make sure MongoDB is running: brew services start mongodb-community")

print("\n🔍 Testing sentence-transformers separately...")
try:
    from sentence_transformers import SentenceTransformer
    print("✅ sentence-transformers available")
    
    # Try to load a model
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("✅ Model loaded successfully")
    
    # Test encoding
    test_text = ["rice", "tea", "coffee"]
    embeddings = model.encode(test_text)
    print(f"✅ Embeddings generated: {embeddings.shape}")
    
except Exception as e:
    print(f"❌ sentence-transformers error: {e}")
    print("   This is expected due to PyTorch compatibility issues")

print("\n🎯 Recommendation: Use MongoDB with simple text search")
