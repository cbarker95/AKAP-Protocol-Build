"""
AKAP Knowledge Node
Core component for processing and managing local knowledge graphs
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import frontmatter
import markdown
import networkx as nx
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class KnowledgeDocument:
    """Represents a single knowledge document"""
    path: str
    title: str
    content: str
    metadata: Dict[str, Any]
    links: List[str]
    concepts: List[str]

class KnowledgeNode:
    """
    Core AKAP component for processing local knowledge
    
    Responsibilities:
    - Parse markdown files from Obsidian vault
    - Build knowledge graphs with relationships
    - Extract semantic patterns using Claude
    - Maintain privacy and sovereignty
    """
    
    def __init__(self, vault_path: str, api_key: Optional[str] = None):
        self.vault_path = Path(vault_path)
        self.graph = nx.DiGraph()
        self.documents: Dict[str, KnowledgeDocument] = {}
        
        # Initialize Claude client
        self.claude = Anthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
        )
        
        logger.info(f"Initialized KnowledgeNode for vault: {vault_path}")
    
    def scan_vault(self) -> List[Path]:
        """Scan the Obsidian vault for markdown files"""
        markdown_files = []
        
        for file_path in self.vault_path.rglob("*.md"):
            # Skip system files and templates
            if not any(skip in str(file_path) for skip in ['.obsidian', '.trash', 'template']):
                markdown_files.append(file_path)
        
        logger.info(f"Found {len(markdown_files)} markdown files")
        return markdown_files
    
    def parse_document(self, file_path: Path) -> KnowledgeDocument:
        """Parse a single markdown document with frontmatter"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
            
            # Extract Obsidian-style links [[link]]
            import re
            links = re.findall(r'\[\[([^\]]+)\]\]', post.content)
            
            # Use Claude to extract key concepts
            concepts = self._extract_concepts(post.content)
            
            doc = KnowledgeDocument(
                path=str(file_path),
                title=post.metadata.get('title', file_path.stem),
                content=post.content,
                metadata=post.metadata,
                links=links,
                concepts=concepts
            )
            
            return doc
            
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return None
    
    def _extract_concepts(self, content: str) -> List[str]:
        """Use Claude to extract key concepts from document content"""
        try:
            # Truncate content if too long
            if len(content) > 3000:
                content = content[:3000] + "..."
            
            response = self.claude.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": f"""Extract 5-10 key concepts from this text. Return only a comma-separated list of concepts:

{content}"""
                }]
            )
            
            concepts_text = response.content[0].text.strip()
            concepts = [c.strip() for c in concepts_text.split(',') if c.strip()]
            
            return concepts[:10]  # Limit to 10 concepts
            
        except Exception as e:
            logger.warning(f"Failed to extract concepts: {e}")
            return []
    
    def build_knowledge_graph(self):
        """Build a NetworkX graph from parsed documents"""
        files = self.scan_vault()
        
        for file_path in files:
            doc = self.parse_document(file_path)
            if doc:
                self.documents[doc.title] = doc
                
                # Add document node
                self.graph.add_node(
                    doc.title,
                    type="document",
                    path=doc.path,
                    concepts=doc.concepts
                )
                
                # Add concept nodes and relationships
                for concept in doc.concepts:
                    self.graph.add_node(concept, type="concept")
                    self.graph.add_edge(doc.title, concept, relationship="contains")
                
                # Add link relationships
                for link in doc.links:
                    if link in self.documents:
                        self.graph.add_edge(doc.title, link, relationship="links_to")
        
        logger.info(f"Built knowledge graph: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
    
    def query_knowledge(self, query: str) -> str:
        """Query the knowledge graph using Claude"""
        # Get relevant documents and concepts
        relevant_content = self._find_relevant_content(query)
        
        try:
            response = self.claude.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": f"""Based on this knowledge base content, answer the following query:

Query: {query}

Relevant content:
{relevant_content}

Provide a comprehensive answer based on the available knowledge."""
                }]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return "Sorry, I couldn't process your query."
    
    def _find_relevant_content(self, query: str, limit: int = 5) -> str:
        """Find documents most relevant to the query"""
        # Simple keyword matching for now
        # TODO: Implement vector similarity search
        
        query_words = set(query.lower().split())
        scored_docs = []
        
        for title, doc in self.documents.items():
            content_words = set(doc.content.lower().split())
            concepts_words = set(' '.join(doc.concepts).lower().split())
            
            # Calculate simple relevance score
            content_score = len(query_words.intersection(content_words))
            concept_score = len(query_words.intersection(concepts_words)) * 2  # Weight concepts higher
            
            total_score = content_score + concept_score
            
            if total_score > 0:
                scored_docs.append((total_score, title, doc))
        
        # Sort by relevance and get top documents
        scored_docs.sort(reverse=True, key=lambda x: x[0])
        top_docs = scored_docs[:limit]
        
        # Combine content
        relevant_content = ""
        for score, title, doc in top_docs:
            relevant_content += f"\n--- {title} ---\n"
            relevant_content += doc.content[:500] + ("..." if len(doc.content) > 500 else "")
            relevant_content += f"\nConcepts: {', '.join(doc.concepts)}\n"
        
        return relevant_content
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph"""
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "documents": len([n for n, d in self.graph.nodes(data=True) if d.get('type') == 'document']),
            "concepts": len([n for n, d in self.graph.nodes(data=True) if d.get('type') == 'concept']),
            "average_degree": sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes() if self.graph.number_of_nodes() > 0 else 0
        }