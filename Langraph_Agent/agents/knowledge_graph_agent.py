"""
Knowledge Graph Agent for enhanced product search
"""
from typing import List, Dict, Any, Tuple
from core.knowledge_graph import KnowledgeGraph


class KnowledgeGraphAgent:
    """Agent that uses knowledge graph for enhanced product search"""
    
    def __init__(self, kg_data_file: str = "knowledge_graph.json"):
        self.knowledge_graph = KnowledgeGraph(kg_data_file)
        print("[AGENT] Knowledge Graph Agent initialized")
    
    def enhance_keywords(self, keywords: List[str]) -> Dict[str, List[str]]:
        """
        Enhance keywords using knowledge graph similarity
        
        Args:
            keywords: Original search keywords
            
        Returns:
            Dictionary mapping original keywords to enhanced keyword lists
        """
        print(f"[KG-AGENT] Enhancing keywords: {keywords}")
        
        enhanced_keywords = {}
        
        # Find similar items for each keyword using knowledge graph
        similar_items = self.knowledge_graph.find_similar_items(keywords, max_depth=2)
        
        for keyword in keywords:
            enhanced_list = [keyword]  # Start with original keyword
            
            if keyword in similar_items:
                for item_id, score in similar_items[keyword]:
                    if item_id in self.knowledge_graph.nodes:
                        node = self.knowledge_graph.nodes[item_id]
                        # Add similar items with good scores
                        if score >= 0.5:
                            enhanced_list.append(node.label.lower())
            
            # Remove duplicates while preserving order
            seen = set()
            enhanced_keywords[keyword] = []
            for item in enhanced_list:
                if item.lower() not in seen:
                    enhanced_keywords[keyword].append(item.lower())
                    seen.add(item.lower())
        
        print(f"[KG-AGENT] Enhanced keywords: {enhanced_keywords}")
        return enhanced_keywords
    
    def get_substitutes(self, product_name: str) -> List[Tuple[str, float]]:
        """
        Get product substitutes when item is out of stock
        
        Args:
            product_name: Name of the product
            
        Returns:
            List of substitute products with similarity scores
        """
        print(f"[KG-AGENT] Finding substitutes for: {product_name}")
        
        similar_items = self.knowledge_graph.find_similar_items([product_name])
        substitutes = []
        
        if product_name in similar_items:
            for item_id, score in similar_items[product_name]:
                if item_id in self.knowledge_graph.nodes:
                    node = self.knowledge_graph.nodes[item_id]
                    # Look for substitute relations specifically
                    for relation in self.knowledge_graph.relations:
                        if (relation.from_node == item_id and 
                            "substitute" in relation.relation_type.lower()):
                            target_node = self.knowledge_graph.nodes.get(relation.to_node)
                            if target_node:
                                substitutes.append((target_node.label, relation.weight))
        
        return sorted(substitutes, key=lambda x: x[1], reverse=True)
    
    def add_custom_knowledge(self, node_data: Dict[str, Any], relations: List[Dict[str, Any]] = None):
        """
        Add custom knowledge to the graph
        
        Args:
            node_data: Node information (id, label, category, attributes)
            relations: List of relations to add
        """
        print(f"[KG-AGENT] Adding custom knowledge: {node_data.get('label', 'Unknown')}")
        
        # Add node
        self.knowledge_graph.add_custom_node(
            node_data.get("id"),
            node_data.get("label"),
            node_data.get("category"),
            node_data.get("attributes", {})
        )
        
        # Add relations if provided
        if relations:
            for rel in relations:
                self.knowledge_graph.add_custom_relation(
                    rel.get("from_node"),
                    rel.get("to_node"),
                    rel.get("relation_type"),
                    rel.get("weight", 1.0)
                )
        
        # Save the updated knowledge graph
        self.knowledge_graph.save_to_file()
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        return self.knowledge_graph.get_stats()
    
    def visualize_connections(self, node_id: str) -> List[str]:
        """
        Get visual representation of node connections
        
        Args:
            node_id: ID of the node to visualize
            
        Returns:
            List of connection descriptions
        """
        connections = []
        
        if node_id not in self.knowledge_graph.nodes:
            return [f"Node '{node_id}' not found in knowledge graph"]
        
        node = self.knowledge_graph.nodes[node_id]
        connections.append(f"🎯 {node.label} ({node.category})")
        
        # Find outgoing relations
        for relation in self.knowledge_graph.adjacency.get(node_id, []):
            target_node = self.knowledge_graph.nodes.get(relation.to_node)
            if target_node:
                connections.append(
                    f"  ➡️  {relation.relation_type} → {target_node.label} (weight: {relation.weight})"
                )
        
        # Find incoming relations
        for relation in self.knowledge_graph.relations:
            if relation.to_node == node_id:
                source_node = self.knowledge_graph.nodes.get(relation.from_node)
                if source_node:
                    connections.append(
                        f"  ⬅️  {source_node.label} → {relation.relation_type} (weight: {relation.weight})"
                    )
        
        return connections
