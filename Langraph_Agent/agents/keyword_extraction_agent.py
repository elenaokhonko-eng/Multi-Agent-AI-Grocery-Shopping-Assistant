"""
Keyword Extraction Agent
"""
import json
from typing import List
from langchain_ollama import ChatOllama


class KeywordExtractionAgent:
    """Agent responsible for extracting food items and products from user input"""
    
    def __init__(self, llm: ChatOllama):
        self.llm = llm
    
    def extract_keywords(self, user_message: str) -> List[str]:
        """
        Extract food items and products from user message using LLM
        
        Args:
            user_message: User's natural language input
            
        Returns:
            List of extracted food items and products
        """
        print(f"[AGENT] Keyword Extraction Agent processing: '{user_message}'")
        
        prompt = f"""Extract food items and products from the following sentence and return them as a JSON object with a "food_items" array.
        
        Sentence: "{user_message}"
        
        Rules:
        - Extract complete food products, not individual words (e.g., "organic rice" not "organic" and "rice")
        - Extract complete product names (e.g., "coconut oil" not "coconut" and "oil")
        - Only include actual food items, groceries, or consumable products
        - Ignore non-food words like "family", "house", "people", etc.
        - Include descriptive adjectives with the food (e.g., "organic rice", "fresh milk", "extra virgin olive oil")
        - Return a valid JSON object
        - Example format: {{"food_items": ["organic milk", "green tea", "olive oil"]}}
        
        Examples:
        - Input: "I need organic rice and coconut oil for cooking"
        - Output: {{"food_items": ["organic rice", "coconut oil"]}}
        
        - Input: "Buy fresh vegetables, milk, and bread for my family"
        - Output: {{"food_items": ["fresh vegetables", "milk", "bread"]}}
        
        Respond with valid JSON only:"""
        
        try:
            response = self.llm.invoke([{"role": "user", "content": prompt}])
            print(f"[AGENT] LLM response: {response.content}")
            
            # Parse JSON response
            response_json = json.loads(response.content.strip())
            food_items = response_json.get("food_items", [])
            
            if not isinstance(food_items, list):
                food_items = [str(food_items)]
                
            print(f"[AGENT] Extracted food items: {food_items}")
            return food_items
            
        except Exception as e:
            print(f"[AGENT] Error in food item extraction: {e}")
            # Fallback: extract likely food words
            import re
            text = user_message.lower()
            # Simple pattern matching for common food items
            food_patterns = [
                r'organic\s+\w+', r'\w+\s+oil', r'\w+\s+rice', r'\w+\s+tea', 
                r'\w+\s+milk', r'\w+\s+bread', r'\w+\s+vegetables'
            ]
            food_items = []
            for pattern in food_patterns:
                matches = re.findall(pattern, text)
                food_items.extend(matches)
            
            if not food_items:
                # Final fallback: extract food-related words
                food_words = ['rice', 'oil', 'tea', 'milk', 'bread', 'vegetables', 'meat', 'fish']
                words = text.split()
                food_items = [word for word in words if word in food_words]
            
            print(f"[AGENT] Fallback food items: {food_items}")
            return food_items
