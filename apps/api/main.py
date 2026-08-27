from fastapi import FastAPI
from sqlmodel import SQLModel, create_engine
import os

from domain.models.core import ShoppingList

app = FastAPI(title="Grocery Shopping Assistant - Singapore")

# This will eventually connect to Postgres
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DB_URL)

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.get("/health")
def health():
    return {"status": "ok", "message": "Singapore Grocery Domain API is running"}
