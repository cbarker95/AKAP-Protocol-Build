#!/usr/bin/env python3
"""
Semantic Search Demo
Demonstrates enhanced AKAP functionality with vector similarity search
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from akap import KnowledgeNode

def main():
    """Demonstrate semantic search capabilities"""
    
    print("🧠 AKAP Protocol - Semantic Search Demo")
    print("=" * 45)
    
    # Initialize Knowledge Node with semantic search
    vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "/Users/user/Documents/Obsidian Vault")
    print(f"📂 Initializing KnowledgeNode with semantic search...")
    
    # Process just a few documents to demonstrate functionality
    node = KnowledgeNode(vault_path, enable_semantic_search=True)
    
    # Scan and show some files
    files = node.scan_vault()
    print(f"📊 Found {len(files)} markdown files")
    
    # Build knowledge graph with semantic embeddings (limiting for demo)
    print(f"\n🕸️  Building knowledge graph and semantic embeddings...")
    print("   (Processing first 10 files for demo purposes)")
    
    # Override to process fewer files for demo
    demo_files = files[:10]
    for file_path in demo_files:
        doc = node.parse_document(file_path)
        if doc:
            node.documents[doc.title] = doc
            
            # Add to graph
            node.graph.add_node(
                doc.title,
                type="document",
                path=doc.path,
                concepts=doc.concepts
            )
            
            # Add concept nodes and relationships
            for concept in doc.concepts:
                node.graph.add_node(concept, type="concept")
                node.graph.add_edge(doc.title, concept, relationship="contains")
            
            # Add link relationships
            for link in doc.links:
                if link in node.documents:
                    node.graph.add_edge(doc.title, link, relationship="links_to")
    
    # Build semantic embeddings
    if node.semantic_processor and node.documents:
        print("   Building vector embeddings...")
        node.semantic_processor.embed_documents(node.documents)
    
    # Get enhanced statistics
    stats = node.get_graph_stats()
    print(f"\n📈 Enhanced Knowledge Graph Statistics:")
    print(f"  - Documents processed: {stats['documents']}")
    print(f"  - Total concepts: {stats['concepts']}")
    print(f"  - Graph nodes: {stats['total_nodes']}")
    print(f"  - Graph edges: {stats['total_edges']}")
    
    if stats.get('semantic_search', {}).get('enabled', False):
        semantic_stats = stats['semantic_search']
        print(f"  - Vector embeddings: {semantic_stats['total_embeddings']}")
        print(f"  - Embedding model: {semantic_stats['embedding_model']}")
    
    # Test semantic search
    print(f"\n🔍 Testing Semantic Search:")
    
    test_queries = [
        "product management and discovery",
        "AI tools for designers",
        "LinkedIn content strategy",
        "design handoff automation"
    ]
    
    for query in test_queries:
        print(f"\n❓ Query: '{query}'")
        
        if node.semantic_processor:
            results = node.semantic_search(query, top_k=3)
            if results:
                print(f"   Top {len(results)} semantic matches:")
                for i, result in enumerate(results[:3], 1):
                    title = result['title']
                    score = result['similarity_score']
                    print(f"   {i}. {title} (similarity: {score:.3f})")
            else:
                print("   No semantic matches found")
        else:
            print("   Semantic search not available")
    
    # Test document similarity
    if node.documents and node.semantic_processor:
        print(f"\n🔗 Testing Document Similarity:")
        
        # Pick the first document as reference
        ref_doc = list(node.documents.keys())[0]
        print(f"   Finding documents similar to: '{ref_doc}'")
        
        similar_docs = node.get_similar_documents(ref_doc, top_k=3)
        if similar_docs:
            print(f"   Top {len(similar_docs)} similar documents:")
            for i, doc in enumerate(similar_docs, 1):
                title = doc['title']
                score = doc['similarity_score']
                print(f"   {i}. {title} (similarity: {score:.3f})")
        else:
            print("   No similar documents found")
    
    # Test enhanced querying
    print(f"\n💡 Testing Enhanced Knowledge Querying:")
    
    query = "How do you implement continuous discovery in product teams?"
    print(f"   Query: {query}")
    
    response = node.query_knowledge(query)
    print(f"   Response: {response[:300]}...")
    
    print(f"\n✅ Semantic search demo complete!")
    print(f"   Enhanced AKAP capabilities demonstrated with vector similarity search")

if __name__ == "__main__":
    main()