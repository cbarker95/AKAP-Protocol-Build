#!/usr/bin/env python3
"""
Basic Knowledge Parsing Example
Demonstrates core AKAP functionality by parsing the Obsidian vault
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from akap import KnowledgeNode

def main():
    """Test basic knowledge parsing functionality"""
    
    print("🧠 AKAP Protocol - Basic Knowledge Parsing Demo")
    print("=" * 50)
    
    # Initialize the Knowledge Node
    vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "/Users/user/Documents/Obsidian Vault")
    
    print(f"📂 Initializing KnowledgeNode for vault: {vault_path}")
    node = KnowledgeNode(vault_path)
    
    # Scan the vault
    print("\n📊 Scanning vault for markdown files...")
    files = node.scan_vault()
    print(f"Found {len(files)} markdown files")
    
    # Build knowledge graph
    print("\n🕸️  Building knowledge graph...")
    node.build_knowledge_graph()
    
    # Get statistics
    stats = node.get_graph_stats()
    print(f"\n📈 Knowledge Graph Statistics:")
    print(f"  - Total nodes: {stats['total_nodes']}")
    print(f"  - Total edges: {stats['total_edges']}")
    print(f"  - Documents: {stats['documents']}")
    print(f"  - Concepts: {stats['concepts']}")
    print(f"  - Average degree: {stats['average_degree']:.2f}")
    
    # Test some sample queries
    print("\n🔍 Testing knowledge queries...")
    
    queries = [
        "What is the AKAP protocol?",
        "Tell me about design handoff automation",
        "What are the LinkedIn content themes?",
        "How does AI-assisted product design work?"
    ]
    
    for query in queries:
        print(f"\n❓ Query: {query}")
        response = node.query_knowledge(query)
        print(f"💡 Answer: {response[:200]}...")
    
    print("\n✅ Knowledge parsing demo complete!")
    print(f"\nYour vault contains {stats['documents']} documents with {stats['concepts']} unique concepts.")

if __name__ == "__main__":
    main()