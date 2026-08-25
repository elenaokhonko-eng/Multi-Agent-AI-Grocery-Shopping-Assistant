import sys
import os
import json

# Add parent dir to path so we can import from Langraph_Agent
sys.path.append(os.path.abspath('..'))
from Langraph_Agent.agents.store_agents import FairPriceAgent, RedMartAgent, ShengSiongAgent, LittleFarmsAgent

if __name__ == '__main__':
    print("Testing Scrapers for keyword: 'eggs'")
    
    mock_llm = None
    
    agents = [
        FairPriceAgent(mock_llm),
        RedMartAgent(mock_llm),
        ShengSiongAgent(mock_llm),
        LittleFarmsAgent(mock_llm)
    ]
    
    for agent in agents:
        print(f"\n--- Running {agent.store_name} Agent ---")
        try:
            result = agent.get_cart(["eggs"])
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"FAILED: {e}")
