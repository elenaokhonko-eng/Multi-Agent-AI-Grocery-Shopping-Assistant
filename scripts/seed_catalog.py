import json
import os
import random
from uuid import uuid4

from sqlmodel import Session, SQLModel, create_engine, select
from domain.models.core import ProductCandidate, StoreSKUPreference

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./grocery.db")
engine = create_engine(DB_URL)

def generate_catalog_for_keyword(keyword: str, store_name: str) -> list[ProductCandidate]:
    """Generates 2-3 realistic mock candidates for a given keyword at a given store."""
    candidates = []
    
    # Capitalize title format
    base_title = keyword.title()
    
    # Premium vs regular sizing/pricing
    variations = [
        {"desc": f"Fresh {base_title} (Standard)", "price": random.randint(300, 1500)},
        {"desc": f"Organic {base_title} (Premium)", "price": random.randint(800, 2500)},
    ]
    
    # Maybe add a bulk option
    if random.choice([True, False]):
        variations.append({"desc": f"Value Pack {base_title}", "price": random.randint(1200, 3500)})

    for i, var in enumerate(variations):
        sku = f"{store_name[:2].upper()}-{keyword.replace(' ', '').upper()}-{i+1}"
        candidates.append(
            ProductCandidate(
                store_name=store_name,
                retailer_sku=sku,
                title=var["desc"],
                price_cents=var["price"],
                image_url=f"https://dummyimage.com/200x200/cccccc/000000&text={keyword.replace(' ', '+')}",
                url=f"https://{store_name.lower().replace(' ', '')}.com/product/{sku}"
            )
        )
    return candidates

def run_seed():
    SQLModel.metadata.create_all(engine)
    
    list_path = os.path.join("Backend", "data", "fixed_grocery_list.json")
    if not os.path.exists(list_path):
        print(f"List not found at {list_path}")
        return
        
    with open(list_path, "r") as f:
        data = json.load(f)
        
    # Extract unique keywords
    keywords = set()
    for item in data.get("weekly_items", []):
        keywords.add(item["keyword"])
    for item in data.get("bi_weekly_items", []):
        keywords.add(item["keyword"])
        
    with Session(engine) as session:
        # Check if already seeded
        existing = session.exec(select(ProductCandidate).limit(1)).first()
        if existing:
            print("Database already seeded with products. Clearing existing data...")
            for candidate in session.exec(select(ProductCandidate)).all():
                session.delete(candidate)
            for pref in session.exec(select(StoreSKUPreference)).all():
                session.delete(pref)
            session.commit()
            
        print(f"Seeding catalog for {len(keywords)} keywords...")
        
        candidates = []
        for kw in keywords:
            for store in ["FairPrice", "Little Farms"]:
                # The fixed list mentions little farms specifically for sockeye salmon
                if kw == "sockeye salmon" and store == "FairPrice":
                    continue
                    
                store_candidates = generate_catalog_for_keyword(kw, store)
                candidates.extend(store_candidates)
                
                # Assign a preference for the first candidate just as an example
                pref = StoreSKUPreference(
                    keyword=kw,
                    store_name=store,
                    preferred_retailer_sku=store_candidates[0].retailer_sku
                )
                session.add(pref)
                
        for c in candidates:
            session.add(c)
            
        session.commit()
        print(f"Successfully seeded {len(candidates)} ProductCandidates!")

if __name__ == "__main__":
    run_seed()
