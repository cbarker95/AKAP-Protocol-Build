"""
AKAP Pattern Extractor
Cross-document pattern recognition and insight generation
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import defaultdict, Counter
import networkx as nx
from anthropic import Anthropic
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class PatternExtractor:
    """
    Extract patterns and generate insights across documents
    
    Capabilities:
    - Cross-document theme identification
    - Concept relationship analysis
    - Knowledge gap detection
    - Insight generation using Claude
    - Evolution pattern tracking
    """
    
    def __init__(self, knowledge_node, api_key: Optional[str] = None):
        """Initialize pattern extractor with knowledge node"""
        self.knowledge_node = knowledge_node
        self.graph = knowledge_node.graph
        self.documents = knowledge_node.documents
        
        # Initialize Claude client for insight generation
        self.claude = Anthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
        )
        
        # Pattern storage
        self.themes = {}
        self.concept_clusters = {}
        self.relationship_patterns = {}
        self.insights = []
        
        logger.info("Initialized PatternExtractor")
    
    def extract_document_themes(self) -> Dict[str, List[str]]:
        """
        Identify major themes across all documents
        
        Returns:
            Dict of {theme_name: [document_titles]}
        """
        
        # Collect all concepts and their document associations
        concept_to_docs = defaultdict(list)
        
        for doc_title, doc in self.documents.items():
            for concept in doc.concepts:
                concept_to_docs[concept.lower()].append(doc_title)
        
        # Find concepts that appear in multiple documents (themes)
        themes = {}
        for concept, doc_list in concept_to_docs.items():
            if len(doc_list) >= 2:  # Concept appears in 2+ documents
                theme_name = concept.replace('_', ' ').title()
                themes[theme_name] = doc_list
        
        # Group similar themes using semantic similarity
        if self.knowledge_node.semantic_processor:
            themes = self._cluster_similar_themes(themes)
        
        self.themes = themes
        logger.info(f"Extracted {len(themes)} cross-document themes")
        return themes
    
    def _cluster_similar_themes(self, themes: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Cluster semantically similar themes together"""
        
        theme_names = list(themes.keys())
        if len(theme_names) < 2:
            return themes
        
        # Use semantic processor to find similar theme names
        clustered_themes = {}
        processed_themes = set()
        
        for theme in theme_names:
            if theme in processed_themes:
                continue
            
            # Find similar theme names
            similar_results = self.knowledge_node.semantic_processor.semantic_search(
                theme, top_k=len(theme_names)
            )
            
            # Group themes with high similarity
            cluster_docs = set(themes[theme])
            cluster_name = theme
            
            for result in similar_results:
                result_theme = result['title']
                if (result_theme in theme_names and 
                    result_theme not in processed_themes and
                    result['similarity_score'] > 0.7):
                    
                    cluster_docs.update(themes[result_theme])
                    processed_themes.add(result_theme)
            
            clustered_themes[cluster_name] = list(cluster_docs)
            processed_themes.add(theme)
        
        return clustered_themes
    
    def analyze_concept_relationships(self) -> Dict[str, Dict[str, int]]:
        """
        Analyze how concepts relate to each other across documents
        
        Returns:
            Dict of {concept: {related_concept: co_occurrence_count}}
        """
        
        concept_cooccurrence = defaultdict(lambda: defaultdict(int))
        
        # For each document, create co-occurrence matrix
        for doc_title, doc in self.documents.items():
            concepts = [c.lower() for c in doc.concepts]
            
            # Count co-occurrences within the same document
            for i, concept1 in enumerate(concepts):
                for j, concept2 in enumerate(concepts):
                    if i != j:  # Don't count self-relationships
                        concept_cooccurrence[concept1][concept2] += 1
        
        # Convert to regular dict for JSON serialization
        relationships = {}
        for concept1, related in concept_cooccurrence.items():
            relationships[concept1] = dict(related)
        
        self.relationship_patterns = relationships
        logger.info(f"Analyzed relationships for {len(relationships)} concepts")
        return relationships
    
    def find_knowledge_gaps(self) -> List[Dict[str, Any]]:
        """
        Identify potential knowledge gaps and areas for expansion
        
        Returns:
            List of knowledge gaps with suggestions
        """
        
        gaps = []
        
        # 1. Find isolated concepts (concepts with few connections)
        concept_connections = defaultdict(int)
        for node in self.graph.nodes():
            if self.graph.nodes[node].get('type') == 'concept':
                concept_connections[node] = self.graph.degree(node)
        
        # Sort by connection count
        isolated_concepts = sorted(concept_connections.items(), key=lambda x: x[1])
        
        for concept, connection_count in isolated_concepts[:5]:  # Top 5 isolated
            if connection_count <= 2:
                gaps.append({
                    'type': 'isolated_concept',
                    'concept': concept,
                    'connection_count': connection_count,
                    'suggestion': f"Consider expanding documentation about '{concept}' or connecting it to related concepts"
                })
        
        # 2. Find missing links between related themes
        themes = self.extract_document_themes()
        for theme1, docs1 in themes.items():
            for theme2, docs2 in themes.items():
                if theme1 != theme2:
                    # Check if themes have overlapping concepts but no direct document links
                    overlap = set(docs1) & set(docs2)
                    if not overlap and len(docs1) > 1 and len(docs2) > 1:
                        gaps.append({
                            'type': 'missing_theme_connection',
                            'themes': [theme1, theme2],
                            'suggestion': f"Consider creating content that bridges '{theme1}' and '{theme2}'"
                        })
        
        logger.info(f"Identified {len(gaps)} potential knowledge gaps")
        return gaps
    
    def generate_insights(self, max_insights: int = 5) -> List[Dict[str, Any]]:
        """
        Generate AI-powered insights from pattern analysis
        
        Args:
            max_insights: Maximum number of insights to generate
            
        Returns:
            List of insights with metadata
        """
        
        # Gather pattern data
        themes = self.extract_document_themes()
        relationships = self.analyze_concept_relationships()
        gaps = self.find_knowledge_gaps()
        
        # Create summary for Claude analysis
        pattern_summary = self._create_pattern_summary(themes, relationships, gaps)
        
        try:
            response = self.claude.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                messages=[{
                    "role": "user",
                    "content": f"""Analyze these knowledge patterns and generate {max_insights} strategic insights:

{pattern_summary}

For each insight, provide:
1. A clear, actionable insight statement
2. The evidence from the patterns that supports it
3. A specific recommendation for action
4. The potential impact if implemented

Format as a structured analysis focusing on strategic opportunities and knowledge synthesis."""
                }]
            )
            
            insights_text = response.content[0].text
            
            # Parse insights (simplified - in production would use more structured parsing)
            insights = self._parse_insights_response(insights_text)
            
            self.insights = insights
            logger.info(f"Generated {len(insights)} strategic insights")
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            return []
    
    def _create_pattern_summary(self, themes: Dict, relationships: Dict, gaps: List) -> str:
        """Create a summary of patterns for Claude analysis"""
        
        summary = "KNOWLEDGE BASE PATTERN ANALYSIS\n\n"
        
        # Document overview
        summary += f"Document Collection Overview:\n"
        summary += f"- Total documents: {len(self.documents)}\n"
        summary += f"- Total concepts: {len([n for n in self.graph.nodes() if self.graph.nodes[n].get('type') == 'concept'])}\n\n"
        
        # Major themes
        summary += "Major Themes (Cross-document patterns):\n"
        for theme, docs in sorted(themes.items(), key=lambda x: len(x[1]), reverse=True)[:8]:
            summary += f"- {theme}: appears in {len(docs)} documents\n"
        summary += "\n"
        
        # Top concept relationships
        summary += "Strongest Concept Relationships:\n"
        relationship_strength = []
        for concept1, related in relationships.items():
            for concept2, count in related.items():
                relationship_strength.append((count, concept1, concept2))
        
        for count, concept1, concept2 in sorted(relationship_strength, reverse=True)[:8]:
            summary += f"- '{concept1}' ↔ '{concept2}': co-occurs {count} times\n"
        summary += "\n"
        
        # Knowledge gaps
        summary += f"Identified Knowledge Gaps ({len(gaps)} total):\n"
        for gap in gaps[:5]:
            summary += f"- {gap['type']}: {gap['suggestion']}\n"
        summary += "\n"
        
        # Sample document titles for context
        summary += "Sample Documents:\n"
        for title in list(self.documents.keys())[:8]:
            summary += f"- {title}\n"
        
        return summary
    
    def _parse_insights_response(self, insights_text: str) -> List[Dict[str, Any]]:
        """Parse Claude's insights response into structured data"""
        
        insights = []
        
        # Simple parsing - look for numbered insights
        sections = re.split(r'\n(?=\d+\.)', insights_text)
        
        for section in sections[1:]:  # Skip first empty section
            if len(section.strip()) > 50:  # Valid insight
                # Extract first line as insight statement
                lines = section.split('\n')
                statement = lines[0].strip()
                
                # Remove numbering
                statement = re.sub(r'^\d+\.\s*', '', statement)
                
                insights.append({
                    'statement': statement,
                    'full_text': section.strip(),
                    'timestamp': self._get_timestamp(),
                    'confidence': 'high'  # Could be enhanced with actual confidence scoring
                })
        
        return insights[:5]  # Limit to 5 insights
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for insights"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def track_evolution_patterns(self) -> Dict[str, Any]:
        """
        Track how knowledge evolves over time (placeholder for future file watching)
        
        Returns:
            Evolution pattern analysis
        """
        
        # This would be enhanced with file modification tracking
        evolution_data = {
            'document_ages': {},
            'concept_introduction_order': [],
            'theme_development': {},
            'growth_patterns': {}
        }
        
        # For now, analyze current state structure
        evolution_data['current_structure'] = {
            'total_documents': len(self.documents),
            'total_concepts': len([n for n in self.graph.nodes() if self.graph.nodes[n].get('type') == 'concept']),
            'average_concepts_per_doc': sum(len(doc.concepts) for doc in self.documents.values()) / len(self.documents) if self.documents else 0,
            'most_connected_concepts': self._get_most_connected_concepts(5)
        }
        
        logger.info("Analyzed evolution patterns for current knowledge state")
        return evolution_data
    
    def _get_most_connected_concepts(self, top_k: int) -> List[Tuple[str, int]]:
        """Get the most connected concepts in the graph"""
        
        concept_degrees = []
        for node in self.graph.nodes():
            if self.graph.nodes[node].get('type') == 'concept':
                degree = self.graph.degree(node)
                concept_degrees.append((node, degree))
        
        return sorted(concept_degrees, key=lambda x: x[1], reverse=True)[:top_k]
    
    def get_pattern_stats(self) -> Dict[str, Any]:
        """Get statistics about extracted patterns"""
        
        return {
            'themes_extracted': len(self.themes),
            'concept_relationships': len(self.relationship_patterns),
            'insights_generated': len(self.insights),
            'most_connected_concepts': self._get_most_connected_concepts(3),
            'pattern_extraction_complete': True
        }