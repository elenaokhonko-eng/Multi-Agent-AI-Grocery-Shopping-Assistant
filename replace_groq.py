import os
import re

agent_dir = "Langraph_Agent"

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Skip if no ChatGroq
    if 'ChatGroq' not in content and 'groq' not in content.lower():
        return

    # Replace langchain import
    content = re.sub(r'from langchain_groq import ChatGroq', r'from langchain_ollama import ChatOllama', content)
    
    # Replace ChatGroq usages (remove api_key if present)
    content = re.sub(r'ChatGroq\(', r'ChatOllama(base_url=Config.OLLAMA_BASE_URL, ', content)
    
    # Remove api_key=..., from ChatOllama calls (since we injected base_url, we just strip api_key)
    content = re.sub(r'api_key=[^,)]*,?\s*', '', content)
    
    # Change model_name to model
    content = re.sub(r'model_name=', r'model=', content)
    
    # Replace ChatGroq type hints
    content = re.sub(r':\s*ChatGroq', r': ChatOllama', content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

for root, _, files in os.walk(agent_dir):
    for file in files:
        if file.endswith('.py'):
            process_file(os.path.join(root, file))

# Specifically handle budget_optimization_agent.py (raw client)
budget_file = os.path.join(agent_dir, 'agents', 'budget_optimization_agent.py')
with open(budget_file, 'r', encoding='utf-8') as f:
    budget_content = f.read()

# Replace groq with openai
budget_content = budget_content.replace('from groq import Groq', 'from openai import OpenAI')
budget_content = budget_content.replace('Groq(api_key=Config.GROQ_API_KEY)', 'OpenAI(base_url=Config.OLLAMA_BASE_URL, api_key="ollama")')
budget_content = budget_content.replace('Groq(', 'OpenAI(')

with open(budget_file, 'w', encoding='utf-8') as f:
    f.write(budget_content)

print("Replacement complete.")
