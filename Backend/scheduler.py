import time
import os
import sys

import schedule

# Add parent directory to path so we can import from Langraph_Agent
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(os.path.join(parent_dir, "Langraph_Agent"))

try:
    from agents.store_agents import LittleFarmsAgent
except ImportError:
    sys.path.append(parent_dir)
    from Langraph_Agent.agents.store_agents import LittleFarmsAgent

def run_little_farms_weekly_job():
    print("\n[Scheduler] Running Little Farms Autonomous Weekly Job...")
    
    # Dummy LLM
    from langchain_ollama import ChatOllama
    from core.config import Config
    dummy_llm = ChatOllama(base_url=Config.OLLAMA_BASE_URL, model=Config.GROQ_MODEL)
    
    agent = LittleFarmsAgent(dummy_llm)
    agent.process_weekly_salmon_order()
    print("[Scheduler] Job complete.\n")

def start_scheduler():
    print("🕒 Starting background scheduler for autonomous tasks...")
    
    # Schedule to run every week
    schedule.every().monday.at("09:00").do(run_little_farms_weekly_job)
    
    # Run once on startup to demonstrate functionality
    try:
        run_little_farms_weekly_job()
    except Exception as e:
        print(f"[Scheduler] Error running job: {e}")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    start_scheduler()
