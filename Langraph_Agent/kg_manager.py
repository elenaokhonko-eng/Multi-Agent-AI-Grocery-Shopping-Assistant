"""
Knowledge Graph Management Interface
Allows users to customize and manage the knowledge graph
"""
import json
from typing import Dict, List, Any
from agents.knowledge_graph_agent import KnowledgeGraphAgent


class KnowledgeGraphManager:
    """Interface for managing and customizing the knowledge graph"""
    
    def __init__(self):
        self.kg_agent = KnowledgeGraphAgent()
        print("🧠 Knowledge Graph Manager initialized")
    
    def display_stats(self):
        """Display knowledge graph statistics"""
        stats = self.kg_agent.get_knowledge_stats()
        
        print("\n" + "="*50)
        print("🧠 KNOWLEDGE GRAPH STATISTICS")
        print("="*50)
        print(f"📊 Total Nodes: {stats['total_nodes']}")
        print(f"🔗 Total Relations: {stats['total_relations']}")
        
        print("\n📂 Categories:")
        for category, count in stats['categories'].items():
            print(f"   • {category}: {count} nodes")
        
        print("\n🔗 Relation Types:")
        for rel_type, count in stats['relation_types'].items():
            print(f"   • {rel_type}: {count} relations")
        print("="*50)
    
    def list_all_nodes(self):
        """List all nodes in the knowledge graph"""
        print("\n" + "="*60)
        print("🧠 ALL KNOWLEDGE GRAPH NODES")
        print("="*60)
        
        nodes_by_category = {}
        for node_id, node in self.kg_agent.knowledge_graph.nodes.items():
            if node.category not in nodes_by_category:
                nodes_by_category[node.category] = []
            nodes_by_category[node.category].append((node_id, node))
        
        for category, nodes in nodes_by_category.items():
            print(f"\n📂 {category.upper()}:")
            for node_id, node in nodes:
                print(f"   • {node.label} (id: {node_id})")
                if node.attributes:
                    print(f"     Attributes: {node.attributes}")
        print("="*60)
    
    def show_node_connections(self, node_id: str):
        """Show connections for a specific node"""
        connections = self.kg_agent.visualize_connections(node_id)
        
        print(f"\n" + "="*50)
        print(f"🧠 CONNECTIONS FOR NODE: {node_id.upper()}")
        print("="*50)
        
        for connection in connections:
            print(connection)
        print("="*50)
    
    def add_custom_product(self):
        """Interactive interface to add a custom product"""
        print("\n🆕 ADD CUSTOM PRODUCT TO KNOWLEDGE GRAPH")
        print("-" * 40)
        
        try:
            # Get product information
            product_id = input("Enter product ID (lowercase, no spaces): ").strip().lower().replace(' ', '_')
            product_label = input("Enter product name/label: ").strip()
            category = input("Enter product category: ").strip()
            
            # Get attributes
            attributes = {}
            print("\nAdd attributes (press Enter without value to finish):")
            while True:
                attr_name = input("Attribute name: ").strip()
                if not attr_name:
                    break
                attr_value = input(f"Value for {attr_name}: ").strip()
                attributes[attr_name] = attr_value
            
            # Create node data
            node_data = {
                "id": product_id,
                "label": product_label,
                "category": category,
                "attributes": attributes
            }
            
            # Get relations
            relations = []
            print(f"\nAdd relations for {product_label} (press Enter without value to finish):")
            while True:
                target_node = input("Target node ID (must exist): ").strip()
                if not target_node:
                    break
                
                if target_node not in self.kg_agent.knowledge_graph.nodes:
                    print(f"❌ Node '{target_node}' does not exist. Available nodes:")
                    self._show_available_nodes()
                    continue
                
                relation_type = input("Relation type (e.g., 'is_type_of', 'substitute_for'): ").strip()
                try:
                    weight = float(input("Weight (0.0-1.0, default 1.0): ").strip() or "1.0")
                except ValueError:
                    weight = 1.0
                
                relations.append({
                    "from_node": product_id,
                    "to_node": target_node,
                    "relation_type": relation_type,
                    "weight": weight
                })
            
            # Add to knowledge graph
            self.kg_agent.add_custom_knowledge(node_data, relations)
            print(f"✅ Successfully added '{product_label}' to knowledge graph!")
            
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled")
        except Exception as e:
            print(f"❌ Error adding product: {e}")
    
    def _show_available_nodes(self):
        """Show available node IDs"""
        print("Available node IDs:")
        for i, node_id in enumerate(sorted(self.kg_agent.knowledge_graph.nodes.keys()), 1):
            print(f"  {i}. {node_id}")
            if i >= 10:  # Limit display
                print(f"  ... and {len(self.kg_agent.knowledge_graph.nodes) - 10} more")
                break
    
    def test_keyword_enhancement(self, test_keywords: List[str]):
        """Test keyword enhancement with current knowledge graph"""
        print(f"\n🧪 TESTING KEYWORD ENHANCEMENT")
        print("="*50)
        print(f"Original keywords: {test_keywords}")
        
        enhanced = self.kg_agent.enhance_keywords(test_keywords)
        
        for keyword, enhanced_list in enhanced.items():
            print(f"\n🔍 '{keyword}' enhanced to:")
            for enhanced_kw in enhanced_list:
                symbol = "🎯" if enhanced_kw == keyword else "🧠"
                print(f"   {symbol} {enhanced_kw}")
        print("="*50)
    
    def export_knowledge_graph(self, filename: str = "kg_export.json"):
        """Export knowledge graph to JSON file"""
        try:
            self.kg_agent.knowledge_graph.save_to_file()
            print(f"✅ Knowledge graph exported to {filename}")
        except Exception as e:
            print(f"❌ Error exporting knowledge graph: {e}")
    
    def interactive_menu(self):
        """Interactive menu for knowledge graph management"""
        while True:
            print("\n" + "="*60)
            print("🧠 KNOWLEDGE GRAPH MANAGEMENT SYSTEM")
            print("="*60)
            print("1. 📊 Show Statistics")
            print("2. 📋 List All Nodes")
            print("3. 🔍 Show Node Connections")
            print("4. 🆕 Add Custom Product")
            print("5. 🧪 Test Keyword Enhancement")
            print("6. 💾 Export Knowledge Graph")
            print("7. 🚪 Exit")
            print("="*60)
            
            try:
                choice = input("Select an option (1-7): ").strip()
                
                if choice == "1":
                    self.display_stats()
                
                elif choice == "2":
                    self.list_all_nodes()
                
                elif choice == "3":
                    node_id = input("Enter node ID to explore: ").strip()
                    self.show_node_connections(node_id)
                
                elif choice == "4":
                    self.add_custom_product()
                
                elif choice == "5":
                    keywords_input = input("Enter test keywords (comma-separated): ").strip()
                    test_keywords = [kw.strip() for kw in keywords_input.split(",") if kw.strip()]
                    if test_keywords:
                        self.test_keyword_enhancement(test_keywords)
                    else:
                        print("❌ No keywords provided")
                
                elif choice == "6":
                    filename = input("Enter filename (default: kg_export.json): ").strip()
                    if not filename:
                        filename = "kg_export.json"
                    self.export_knowledge_graph(filename)
                
                elif choice == "7":
                    print("👋 Goodbye!")
                    break
                
                else:
                    print("❌ Invalid option. Please select 1-7.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


def main():
    """Main entry point for knowledge graph management"""
    manager = KnowledgeGraphManager()
    manager.interactive_menu()


if __name__ == "__main__":
    main()
