#!/usr/bin/env python3
"""
Pattern Extraction Demo
Demonstrates AKAP's cross-document pattern recognition and insight generation
"""

import os
import sys
import json
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from akap import KnowledgeNode

def main():
    """Demonstrate pattern extraction and insight generation"""
    
    print("🧠 AKAP Protocol - Pattern Extraction & Insight Generation")
    print("=" * 60)
    
    # Initialize Knowledge Node with full capabilities
    vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "/Users/user/Documents/Obsidian Vault")
    print(f"📂 Initializing enhanced KnowledgeNode...")
    
    node = KnowledgeNode(vault_path, enable_semantic_search=True)
    
    # Build knowledge graph with limited set for demo
    print(f"🕸️  Building knowledge graph with pattern extraction...")
    files = node.scan_vault()
    print(f"   Processing first 15 files for comprehensive demo")
    
    # Process documents
    demo_files = files[:15]
    for file_path in demo_files:
        doc = node.parse_document(file_path)
        if doc:
            node.documents[doc.title] = doc
    
    # Build graph structure
    for doc_title, doc in node.documents.items():
        # Add document node
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
    
    # Initialize semantic processor and pattern extractor
    if node.semantic_processor and node.documents:
        print("   Building vector embeddings...")
        node.semantic_processor.embed_documents(node.documents)
    
    # Initialize pattern extractor
    if node.documents:
        from akap import PatternExtractor
        node.pattern_extractor = PatternExtractor(node)
    
    # Display enhanced statistics
    stats = node.get_graph_stats()
    print(f"\n📈 Enhanced Knowledge Graph Statistics:")
    print(f"  - Documents: {stats['documents']}")
    print(f"  - Concepts: {stats['concepts']}")
    print(f"  - Graph edges: {stats['total_edges']}")
    print(f"  - Semantic search: {'✅' if stats.get('semantic_search', {}).get('enabled', False) else '❌'}")
    print(f"  - Pattern extraction: {'✅' if stats.get('pattern_extraction', {}).get('enabled', False) else '❌'}")
    
    # Extract and display themes
    print(f"\n🎨 Cross-Document Themes Analysis:")
    themes = node.get_themes()
    
    if themes:
        print(f"   Found {len(themes)} major themes:")
        for theme, docs in sorted(themes.items(), key=lambda x: len(x[1]), reverse=True)[:8]:
            print(f"   • {theme}: {len(docs)} documents")
            if len(docs) <= 3:
                print(f"     └─ {', '.join(docs)}")
            else:
                print(f"     └─ {', '.join(docs[:2])}, ... (+{len(docs)-2} more)")
    else:
        print("   No cross-document themes found")
    
    # Analyze knowledge gaps
    print(f"\n🔍 Knowledge Gap Analysis:")
    gaps = node.find_knowledge_gaps()
    
    if gaps:
        print(f"   Identified {len(gaps)} potential gaps:")
        for i, gap in enumerate(gaps[:5], 1):
            print(f"   {i}. {gap['type'].replace('_', ' ').title()}")
            print(f"      └─ {gap['suggestion']}")
    else:
        print("   No significant knowledge gaps identified")
    
    # Generate strategic insights
    print(f"\n💡 AI-Generated Strategic Insights:")
    print("   Analyzing patterns to generate insights...")
    
    insights = node.get_insights(max_insights=3)
    
    if insights:
        print(f"   Generated {len(insights)} strategic insights:")
        for i, insight in enumerate(insights, 1):
            statement = insight['statement'][:100] + "..." if len(insight['statement']) > 100 else insight['statement']
            print(f"\n   {i}. {statement}")
            print(f"      Confidence: {insight.get('confidence', 'medium').title()}")
    else:
        print("   Unable to generate insights at this time")
    
    # Full pattern extraction
    print(f"\n🔬 Comprehensive Pattern Extraction:")
    patterns = node.extract_patterns()
    
    if patterns:
        print(f"   📊 Pattern Analysis Complete:")
        print(f"   • Themes identified: {len(patterns.get('themes', {}))}")
        print(f"   • Concept relationships: {len(patterns.get('concept_relationships', {}))}")
        print(f"   • Knowledge gaps: {len(patterns.get('knowledge_gaps', []))}")
        print(f"   • Strategic insights: {len(patterns.get('insights', []))}")
        
        # Show top concept relationships
        relationships = patterns.get('concept_relationships', {})
        if relationships:
            print(f"\n   🔗 Strongest Concept Relationships:")
            relationship_strength = []
            for concept1, related in relationships.items():
                for concept2, count in related.items():
                    relationship_strength.append((count, concept1, concept2))
            
            for count, concept1, concept2 in sorted(relationship_strength, reverse=True)[:5]:
                print(f"   • '{concept1}' ↔ '{concept2}': {count} co-occurrences")
    
    # Evolution patterns
    evolution = patterns.get('evolution_patterns', {})
    if evolution and 'current_structure' in evolution:
        structure = evolution['current_structure']
        print(f"\n📈 Knowledge Evolution Analysis:")
        print(f"   • Average concepts per document: {structure.get('average_concepts_per_doc', 0):.1f}")
        
        top_concepts = structure.get('most_connected_concepts', [])
        if top_concepts:
            print(f"   • Most connected concepts:")
            for concept, connections in top_concepts[:3]:
                print(f"     └─ {concept}: {connections} connections")
    
    # Export insights for external use
    print(f"\n📤 Exporting Analysis Results:")
    
    # Create summary export
    export_data = {
        'analysis_type': 'AKAP Pattern Extraction',
        'vault_path': vault_path,
        'documents_analyzed': len(node.documents),
        'statistics': stats,
        'themes': themes,
        'insights': insights[:3] if insights else [],
        'knowledge_gaps': gaps[:5] if gaps else [],
        'timestamp': patterns.get('evolution_patterns', {}).get('current_structure', {}).get('analysis_timestamp', 'unknown')
    }
    
    # Save to data directory
    export_path = Path("./data/pattern_analysis.json")
    export_path.parent.mkdir(exist_ok=True)
    
    with open(export_path, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"   ✅ Analysis exported to: {export_path}")
    print(f"   📊 {len(export_data)} data categories captured")
    
    print(f"\n🎉 Pattern Extraction Demo Complete!")
    print(f"   Enhanced AKAP capabilities demonstrated:")
    print(f"   • Cross-document theme identification")
    print(f"   • AI-powered insight generation")  
    print(f"   • Knowledge gap analysis")
    print(f"   • Concept relationship mapping")
    print(f"   • Strategic pattern recognition")

if __name__ == "__main__":
    main()