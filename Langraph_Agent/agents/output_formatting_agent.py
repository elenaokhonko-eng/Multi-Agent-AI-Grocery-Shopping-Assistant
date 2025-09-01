"""
Output Formatting Agent
"""
from typing import Dict, List, Any


class OutputFormattingAgent:
    """Agent responsible for formatting and displaying results"""
    
    def format_results(self, results: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Format product search results for display
        
        Args:
            results: Dictionary mapping keywords to product data
            
        Returns:
            Formatted string for display
        """
        print(f"[AGENT] Output Formatting Agent processing {len(results)} keyword results")
        
        if not results:
            return "\nNo results found."
        
        output = "\n" + "="*60 + "\n"
        output += "KEYWORD MATCHES WITH DETAILED INFORMATION\n"
        output += "="*60 + "\n"
        
        for kw, items in results.items():
            output += f"\n🔍 KEYWORD: {kw.upper()}\n"
            output += "-" * 40 + "\n"
            
            if not items:
                output += "   No items found for this keyword.\n\n"
                continue
            
            for i, item in enumerate(items, 1):
                output += f"\n{i}. {item.get('title', 'N/A')}\n"
                
                if 'error' in item:
                    output += f"   ❌ Error: {item.get('error', 'Unknown error')}\n"
                else:
                    output += f"   💰 Price: LKR {item.get('price_lkr', 0):.2f}\n"
                    output += f"   🌐 Website: {item.get('website', 'N/A')}\n"
                    output += f"   🔗 URL: {item.get('source_url', 'N/A')}\n"
                    output += f"   📦 Collection: {item.get('collection', 'N/A')}\n"
                    
                    if item.get('similarity_score'):
                        output += f"   📊 Similarity: {item.get('similarity_score', 0):.2f}\n"
                
                output += "\n"
        
        output += "="*60 + "\n"
        return output
