"""
Knowledge Graph for Product Search Enhancement
"""
import json
import os
from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class KnowledgeNode:
    """Represents a node in the knowledge graph"""
    id: str
    label: str
    category: str
    attributes: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}


@dataclass
class KnowledgeRelation:
    """Represents a relationship between nodes"""
    from_node: str
    to_node: str
    relation_type: str
    weight: float = 1.0


class KnowledgeGraph:
    """Knowledge Graph for product search enhancement"""
    
    def __init__(self, data_file: str = "knowledge_graph.json"):
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.relations: List[KnowledgeRelation] = []
        self.adjacency: Dict[str, List[KnowledgeRelation]] = defaultdict(list)
        self.data_file = data_file
        
        # Initialize with sample data if file doesn't exist
        if not os.path.exists(data_file):
            self._initialize_sample_data()
            self.save_to_file()
        else:
            self.load_from_file()
    
    def _initialize_sample_data(self):
        """Initialize the knowledge graph with sample data"""
        print("[KG] Initializing knowledge graph with sample data...")
        
        # Add sample nodes
        sample_nodes = [
            # Rice varieties
            KnowledgeNode("rice", "Rice", "staple_food", {"type": "grain", "cooking_time": "15-20min"}),
            KnowledgeNode("samba_rice", "Samba Rice", "rice_variety", {"type": "long_grain", "origin": "Sri Lanka"}),
            KnowledgeNode("nadu_rice", "Nadu Rice", "rice_variety", {"type": "medium_grain", "origin": "Sri Lanka"}),
            KnowledgeNode("basmati_rice", "Basmati Rice", "rice_variety", {"type": "aromatic", "origin": "India"}),
            
            # Dairy products
            KnowledgeNode("dairy", "Dairy", "food_category", {"perishable": True}),
            KnowledgeNode("milk", "Milk", "dairy_product", {"fat_content": "variable", "shelf_life": "3-5 days"}),
            KnowledgeNode("cheese", "Cheese", "dairy_product", {"aged": True, "shelf_life": "weeks"}),
            KnowledgeNode("yogurt", "Yogurt", "dairy_product", {"probiotic": True, "shelf_life": "1-2 weeks"}),
            
            # Brands and substitutes
            KnowledgeNode("milo_400g", "Milo 400g", "beverage_product", {"brand": "Milo", "size": "400g"}),
            KnowledgeNode("nestomalt_400g", "Nestomalt 400g", "beverage_product", {"brand": "Nestomalt", "size": "400g"}),
            KnowledgeNode("milo_200g", "Milo 200g", "beverage_product", {"brand": "Milo", "size": "200g"}),
            
            # Tea varieties
            KnowledgeNode("tea", "Tea", "beverage", {"caffeine": True, "hot_drink": True}),
            KnowledgeNode("black_tea", "Black Tea", "tea_variety", {"oxidation": "full", "strength": "strong"}),
            KnowledgeNode("green_tea", "Green Tea", "tea_variety", {"oxidation": "minimal", "antioxidants": "high"}),
            KnowledgeNode("herbal_tea", "Herbal Tea", "tea_variety", {"caffeine": False, "medicinal": True}),
        ]
        
        for node in sample_nodes:
            self.add_node(node)
        
        # Add sample relations
        sample_relations = [
            # Rice relationships
            KnowledgeRelation("samba_rice", "rice", "is_type_of", 1.0),
            KnowledgeRelation("nadu_rice", "rice", "is_type_of", 1.0),
            KnowledgeRelation("basmati_rice", "rice", "is_type_of", 1.0),
            
            # Dairy relationships
            KnowledgeRelation("milk", "dairy", "belongs_to", 1.0),
            KnowledgeRelation("cheese", "dairy", "belongs_to", 1.0),
            KnowledgeRelation("yogurt", "dairy", "belongs_to", 1.0),
            KnowledgeRelation("cheese", "milk", "made_from", 0.9),
            KnowledgeRelation("yogurt", "milk", "made_from", 0.8),
            
            # Brand substitutions (when out of stock)
            KnowledgeRelation("milo_400g", "nestomalt_400g", "substitute_brand", 0.8),
            KnowledgeRelation("nestomalt_400g", "milo_400g", "substitute_brand", 0.8),
            KnowledgeRelation("milo_400g", "milo_200g", "substitute_package", 0.7),
            
            # Tea relationships
            KnowledgeRelation("black_tea", "tea", "is_type_of", 1.0),
            KnowledgeRelation("green_tea", "tea", "is_type_of", 1.0),
            KnowledgeRelation("herbal_tea", "tea", "is_type_of", 1.0),
        ]
        
        for relation in sample_relations:
            self.add_relation(relation)
    
    def add_node(self, node: KnowledgeNode):
        """Add a node to the knowledge graph"""
        self.nodes[node.id] = node
        print(f"[KG] Added node: {node.label} ({node.category})")
    
    def add_relation(self, relation: KnowledgeRelation):
        """Add a relation to the knowledge graph"""
        self.relations.append(relation)
        self.adjacency[relation.from_node].append(relation)
        print(f"[KG] Added relation: {relation.from_node} -> {relation.to_node} ({relation.relation_type})")
    
    def find_similar_items(self, query_terms: List[str], max_depth: int = 2) -> Dict[str, List[Tuple[str, float]]]:
        """
        Find similar items using knowledge graph traversal
        
        Args:
            query_terms: List of search terms
            max_depth: Maximum depth for graph traversal
            
        Returns:
            Dictionary mapping query terms to similar items with scores
        """
        print(f"[KG] Finding similar items for: {query_terms}")
        results = {}
        
        for term in query_terms:
            similar_items = []
            
            # Find exact matches first
            exact_matches = self._find_exact_matches(term)
            for match_id in exact_matches:
                similar_items.append((match_id, 1.0))
            
            # Find related items through graph traversal
            if exact_matches:
                for match_id in exact_matches:
                    related = self._traverse_graph(match_id, max_depth)
                    similar_items.extend(related)
            else:
                # If no exact match, try fuzzy matching
                fuzzy_matches = self._fuzzy_match(term)
                similar_items.extend(fuzzy_matches)
            
            # Remove duplicates and sort by score
            unique_items = {}
            for item_id, score in similar_items:
                if item_id not in unique_items or unique_items[item_id] < score:
                    unique_items[item_id] = score
            
            sorted_items = sorted(unique_items.items(), key=lambda x: x[1], reverse=True)
            results[term] = sorted_items[:10]  # Top 10 similar items
            
            print(f"[KG] Found {len(results[term])} similar items for '{term}'")
        
        return results
    
    def _find_exact_matches(self, term: str) -> List[str]:
        """Find exact matches for a term"""
        matches = []
        term_lower = term.lower()
        
        for node_id, node in self.nodes.items():
            if (term_lower in node.label.lower() or 
                term_lower in node.id.lower() or
                term_lower in node.category.lower()):
                matches.append(node_id)
        
        return matches
    
    def _fuzzy_match(self, term: str) -> List[Tuple[str, float]]:
        """Perform fuzzy matching for terms"""
        matches = []
        term_lower = term.lower()
        
        for node_id, node in self.nodes.items():
            score = 0.0
            
            # Check label similarity
            if term_lower in node.label.lower():
                score = max(score, 0.8)
            
            # Check category similarity
            if term_lower in node.category.lower():
                score = max(score, 0.6)
            
            # Check attribute similarity
            for attr_key, attr_value in node.attributes.items():
                if isinstance(attr_value, str) and term_lower in attr_value.lower():
                    score = max(score, 0.4)
            
            if score > 0:
                matches.append((node_id, score))
        
        return matches
    
    def _traverse_graph(self, start_node: str, max_depth: int) -> List[Tuple[str, float]]:
        """Traverse the graph to find related items"""
        visited = set()
        related_items = []
        
        def dfs(node_id: str, depth: int, accumulated_weight: float):
            if depth >= max_depth or node_id in visited:
                return
            
            visited.add(node_id)
            
            for relation in self.adjacency.get(node_id, []):
                target_node = relation.to_node
                new_weight = accumulated_weight * relation.weight
                
                if target_node not in visited:
                    related_items.append((target_node, new_weight))
                    dfs(target_node, depth + 1, new_weight)
        
        dfs(start_node, 0, 1.0)
        return related_items
    
    def get_suggestions(self, term: str) -> List[str]:
        """Get product suggestions based on knowledge graph"""
        similar_items = self.find_similar_items([term])
        suggestions = []
        
        if term in similar_items:
            for item_id, score in similar_items[term]:
                if item_id in self.nodes:
                    node = self.nodes[item_id]
                    suggestions.append(f"{node.label} (score: {score:.2f})")
        
        return suggestions
    
    def save_to_file(self):
        """Save knowledge graph to JSON file"""
        data = {
            "nodes": {node_id: asdict(node) for node_id, node in self.nodes.items()},
            "relations": [asdict(rel) for rel in self.relations]
        }
        
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"[KG] Knowledge graph saved to {self.data_file}")
    
    def load_from_file(self):
        """Load knowledge graph from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            # Load nodes
            for node_id, node_data in data.get("nodes", {}).items():
                node = KnowledgeNode(**node_data)
                self.nodes[node_id] = node
            
            # Load relations
            for rel_data in data.get("relations", []):
                relation = KnowledgeRelation(**rel_data)
                self.relations.append(relation)
                self.adjacency[relation.from_node].append(relation)
            
            print(f"[KG] Knowledge graph loaded from {self.data_file}")
            print(f"[KG] Loaded {len(self.nodes)} nodes and {len(self.relations)} relations")
            
        except Exception as e:
            print(f"[KG] Error loading knowledge graph: {e}")
            self._initialize_sample_data()
    
    def add_custom_node(self, node_id: str, label: str, category: str, attributes: Dict[str, Any] = None):
        """Add a custom node to the knowledge graph"""
        node = KnowledgeNode(node_id, label, category, attributes or {})
        self.add_node(node)
    
    def add_custom_relation(self, from_node: str, to_node: str, relation_type: str, weight: float = 1.0):
        """Add a custom relation to the knowledge graph"""
        if from_node in self.nodes and to_node in self.nodes:
            relation = KnowledgeRelation(from_node, to_node, relation_type, weight)
            self.add_relation(relation)
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        categories = defaultdict(int)
        relation_types = defaultdict(int)
        
        for node in self.nodes.values():
            categories[node.category] += 1
        
        for relation in self.relations:
            relation_types[relation.relation_type] += 1
        
        return {
            "total_nodes": len(self.nodes),
            "total_relations": len(self.relations),
            "categories": dict(categories),
            "relation_types": dict(relation_types)
        }
