"""
Output Formatting Agent
"""
from typing import Dict, List, Any


class OutputFormattingAgent:
    """Agent responsible for formatting and displaying results"""
    
    def format_results(self, results: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Format product search results for display with knowledge graph enhancements
        
        Args:
            results: Dictionary mapping keywords to product data
            
        Returns:
            Formatted string for display
        """
        print(f"[AGENT] Output Formatting Agent processing {len(results)} keyword results")
        
        if not results:
            return "\nNo results found."
        
        output = "\n" + "="*70 + "\n"
        output += "🧠 KNOWLEDGE GRAPH ENHANCED PRODUCT SEARCH RESULTS\n"
        output += "="*70 + "\n"
        
        for kw, items in results.items():
            output += f"\n🔍 KEYWORD: {kw.upper()}\n"
            output += "-" * 50 + "\n"
            
            if not items:
                output += "   No items found for this keyword.\n\n"
                continue
            
            # Separate original and enhanced results
            original_results = [item for item in items if not item.get('kg_enhanced', False)]
            enhanced_results = [item for item in items if item.get('kg_enhanced', False)]
            
            # Display original results first
            if original_results:
                output += "📍 DIRECT MATCHES:\n"
                for i, item in enumerate(original_results, 1):
                    output += self._format_single_item(item, i)
            
            # Display knowledge graph enhanced results
            if enhanced_results:
                output += "\n🧠 KNOWLEDGE GRAPH ENHANCED RESULTS:\n"
                for i, item in enumerate(enhanced_results, len(original_results) + 1):
                    output += self._format_single_item(item, i)
                    output += f"   🔗 Enhanced from: {item.get('original_query', 'N/A')}\n\n"
        
        output += "="*70 + "\n"
        output += "🧠 Results enhanced using Knowledge Graph technology\n"
        output += "="*70 + "\n"
        return output
    
    def _format_single_item(self, item: Dict[str, Any], index: int) -> str:
        """Format a single item for display"""
        output = f"\n{index}. {item.get('title', 'N/A')}\n"
        
        if 'error' in item:
            output += f"   ❌ Error: {item.get('error', 'Unknown error')}\n"
        else:
            output += f"   💰 Price: LKR {item.get('price_lkr', 0):.2f}\n"
            output += f"   🌐 Website: {item.get('website', 'N/A')}\n"
            output += f"   🔗 URL: {item.get('source_url', 'N/A')}\n"
            output += f"   📦 Collection: {item.get('collection', 'N/A')}\n"
            
            if item.get('similarity_score'):
                output += f"   📊 Similarity: {item.get('similarity_score', 0):.2f}\n"
            
            if item.get('kg_enhanced'):
                output += f"   🧠 KG Enhanced: Yes\n"
        
        output += "\n"
        return output
