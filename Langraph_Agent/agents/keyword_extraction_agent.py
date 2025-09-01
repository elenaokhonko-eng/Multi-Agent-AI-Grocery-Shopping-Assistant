"""
Keyword Extraction Agent
"""
import json
from typing import List
from langchain_groq import ChatGroq


class KeywordExtractionAgent:
    """Agent responsible for extracting keywords from user input"""
    
    def __init__(self, llm: ChatGroq):
        self.llm = llm
    
    def extract_keywords(self, user_message: str) -> List[str]:
        """
        Extract keywords from user message using LLM
        
        Args:
            user_message: User's natural language input
            
        Returns:
            List of extracted keywords
        """
        print(f"[AGENT] Keyword Extraction Agent processing: '{user_message}'")
        
        prompt = f"""Extract only the important keywords from the following sentence and return them as a JSON object with a "keywords" array.
        
        Sentence: "{user_message}"
        
        Rules:
        - Extract only nouns and important adjectives
        - Ignore common words like 'I', 'need', 'want', 'and', 'the', 'a', etc.
        - Return a valid JSON object
        - Example format: {{"keywords": ["milk", "tea", "organic"]}}
        
        Respond with valid JSON only:"""
        
        try:
            response = self.llm.invoke([{"role": "user", "content": prompt}])
            print(f"[AGENT] LLM response: {response.content}")
            
            # Parse JSON response
            response_json = json.loads(response.content.strip())
            keywords = response_json.get("keywords", [])
            
            if not isinstance(keywords, list):
                keywords = [str(keywords)]
                
            print(f"[AGENT] Extracted keywords: {keywords}")
            return keywords
            
        except Exception as e:
            print(f"[AGENT] Error in keyword extraction: {e}")
            # Fallback: simple word extraction
            words = user_message.lower().split()
            keywords = [word for word in words if word.isalpha() and len(word) > 2]
            print(f"[AGENT] Fallback keywords: {keywords}")
            return keywords
