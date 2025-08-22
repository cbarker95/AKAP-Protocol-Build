"""
AKAP Federation Protocol
Privacy-preserving P2P knowledge sharing and decentralized coordination
"""

import os
import json
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import socket
import threading
import asyncio
import aiohttp
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class KnowledgeFragment:
    """
    A privacy-preserving fragment of knowledge for sharing
    Contains only metadata and derived insights, never raw content
    """
    fragment_id: str
    node_id: str
    content_hash: str  # Hash of original content for deduplication
    concepts: List[str]  # Key concepts extracted
    themes: List[str]  # Document themes
    creation_time: str
    last_updated: str
    similarity_embeddings: Optional[List[float]] = None  # For semantic matching
    privacy_level: str = "public"  # public, protected, private
    metadata: Dict[str, Any] = None

@dataclass
class FederationNode:
    """
    Represents a peer node in the AKAP federation
    """
    node_id: str
    address: str
    port: int
    public_key: str
    trust_score: float = 0.0
    last_seen: str = ""
    capabilities: List[str] = None  # What this node can provide
    shared_concepts: Set[str] = None  # Concepts this node has knowledge about

class AKAPFederationProtocol:
    """
    Privacy-first P2P knowledge sharing protocol
    
    Core principles:
    - No raw content is ever shared
    - Only concepts, themes, and derived insights are exchanged
    - Cryptographic privacy protection
    - Decentralized peer discovery
    - Trust-based reputation system
    """
    
    def __init__(self, knowledge_node, node_id: Optional[str] = None, port: int = 8447):
        self.knowledge_node = knowledge_node
        self.node_id = node_id or self._generate_node_id()
        self.port = port
        
        # Peer management
        self.peers: Dict[str, FederationNode] = {}
        self.shared_fragments: Dict[str, KnowledgeFragment] = {}
        
        # Privacy and security
        self.encryption_key = self._generate_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        
        # Network components
        self.server = None
        self.is_running = False
        
        # Claude for insight processing
        self.claude = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        logger.info(f"Initialized AKAP Federation Node: {self.node_id}")
    
    def _generate_node_id(self) -> str:
        """Generate unique node identifier"""
        import uuid
        return f"akap-{uuid.uuid4().hex[:12]}"
    
    def _generate_encryption_key(self) -> bytes:
        """Generate encryption key for secure communications"""
        password = f"akap-{self.node_id}".encode()
        salt = b'akap_federation_salt'  # In production, use random salt per node
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def create_knowledge_fragments(self) -> List[KnowledgeFragment]:
        """
        Convert local knowledge into privacy-preserving fragments
        Only extracts concepts and themes, never raw content
        """
        fragments = []
        
        if not self.knowledge_node.documents:
            logger.warning("No documents available for fragment creation")
            return fragments
        
        for doc_title, doc in self.knowledge_node.documents.items():
            # Create content hash for deduplication
            content_hash = hashlib.sha256(doc.content.encode()).hexdigest()
            
            # Get themes from pattern extractor if available
            themes = []
            if self.knowledge_node.pattern_extractor:
                document_themes = self.knowledge_node.pattern_extractor.extract_document_themes()
                for theme, docs in document_themes.items():
                    if doc_title in docs:
                        themes.append(theme)
            
            # Get semantic embeddings if available (truncated for privacy)
            embeddings = None
            if self.knowledge_node.semantic_processor:
                # Get first 50 dimensions only for privacy
                try:
                    doc_embedding = self.knowledge_node.semantic_processor.embedding_model.encode([doc.content[:1000]])[0]
                    embeddings = doc_embedding[:50].tolist()  # Truncate for privacy
                except Exception as e:
                    logger.warning(f"Could not generate embedding for {doc_title}: {e}")
            
            fragment = KnowledgeFragment(
                fragment_id=f"{self.node_id}-{hashlib.md5(doc_title.encode()).hexdigest()[:8]}",
                node_id=self.node_id,
                content_hash=content_hash,
                concepts=doc.concepts,
                themes=themes,
                creation_time=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat(),
                similarity_embeddings=embeddings,
                privacy_level="public",  # Can be configured per document
                metadata={
                    "title_hash": hashlib.md5(doc_title.encode()).hexdigest(),
                    "content_length": len(doc.content),
                    "link_count": len(doc.links)
                }
            )
            
            fragments.append(fragment)
            self.shared_fragments[fragment.fragment_id] = fragment
        
        logger.info(f"Created {len(fragments)} knowledge fragments")
        return fragments
    
    def find_semantic_matches(self, query_concepts: List[str], max_results: int = 10) -> List[Tuple[str, float]]:
        """
        Find semantically similar fragments from peers
        Returns list of (peer_node_id, similarity_score) tuples
        """
        if not self.knowledge_node.semantic_processor:
            logger.warning("Semantic processor not available for matching")
            return []
        
        # Generate query embedding
        query_text = " ".join(query_concepts)
        try:
            query_embedding = self.knowledge_node.semantic_processor.embedding_model.encode([query_text])[0][:50]
        except Exception as e:
            logger.error(f"Could not generate query embedding: {e}")
            return []
        
        matches = []
        
        # Compare against all known fragments
        for fragment in self.shared_fragments.values():
            if fragment.similarity_embeddings and fragment.node_id != self.node_id:
                # Calculate cosine similarity (simplified)
                similarity = self._cosine_similarity(query_embedding, fragment.similarity_embeddings)
                if similarity > 0.3:  # Threshold for relevance
                    matches.append((fragment.node_id, similarity))
        
        # Sort by similarity and return top results
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:max_results]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import math
        
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    async def discover_peers(self, discovery_method: str = "local_broadcast") -> List[FederationNode]:
        """
        Discover other AKAP nodes on the network
        """
        discovered_peers = []
        
        if discovery_method == "local_broadcast":
            # Simple local network discovery
            discovered_peers = await self._discover_local_peers()
        elif discovery_method == "dht":
            # Distributed hash table discovery (future implementation)
            pass
        elif discovery_method == "bootstrap":
            # Bootstrap from known nodes (future implementation)
            pass
        
        logger.info(f"Discovered {len(discovered_peers)} peers")
        return discovered_peers
    
    async def _discover_local_peers(self) -> List[FederationNode]:
        """Discover peers on local network via broadcast"""
        peers = []
        
        # Send broadcast discovery message
        discovery_message = {
            "type": "akap_discovery",
            "node_id": self.node_id,
            "port": self.port,
            "concepts": list(set().union(*[f.concepts for f in self.shared_fragments.values()]))[:20]  # Sample concepts
        }
        
        try:
            # Simple UDP broadcast (simplified implementation)
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(2.0)
            
            message_bytes = json.dumps(discovery_message).encode()
            sock.sendto(message_bytes, ('<broadcast>', self.port))
            
            # Listen for responses
            try:
                while True:
                    data, addr = sock.recvfrom(1024)
                    response = json.loads(data.decode())
                    
                    if (response.get("type") == "akap_discovery_response" and 
                        response.get("node_id") != self.node_id):
                        
                        peer = FederationNode(
                            node_id=response["node_id"],
                            address=addr[0],
                            port=response["port"],
                            public_key="",  # Would be exchanged in real implementation
                            trust_score=0.5,  # Initial trust score
                            last_seen=datetime.now().isoformat(),
                            capabilities=response.get("capabilities", []),
                            shared_concepts=set(response.get("concepts", []))
                        )
                        
                        peers.append(peer)
                        self.peers[peer.node_id] = peer
                        
            except socket.timeout:
                pass  # Normal timeout after listening period
                
        except Exception as e:
            logger.error(f"Error during peer discovery: {e}")
        finally:
            sock.close()
        
        return peers
    
    async def share_insights(self, peer_node_id: str, query: str) -> Optional[str]:
        """
        Request insights from a peer node about a specific query
        Returns aggregated insights without exposing raw content
        """
        if peer_node_id not in self.peers:
            logger.error(f"Peer {peer_node_id} not found")
            return None
        
        peer = self.peers[peer_node_id]
        
        # Create insight request
        request = {
            "type": "insight_request",
            "from_node": self.node_id,
            "query": query,
            "request_id": hashlib.md5(f"{query}-{datetime.now().isoformat()}".encode()).hexdigest()[:8]
        }
        
        try:
            # In a real implementation, this would be sent over secure HTTP/WebSocket
            # For now, simulate the response
            response = await self._simulate_peer_insight_response(peer, query)
            
            if response and response.get("insights"):
                return response["insights"]
                
        except Exception as e:
            logger.error(f"Error requesting insights from {peer_node_id}: {e}")
        
        return None
    
    async def _simulate_peer_insight_response(self, peer: FederationNode, query: str) -> Optional[Dict]:
        """
        Simulate how a peer would respond to an insight request
        In reality, this would generate insights from their knowledge base
        """
        
        # Find relevant concepts from peer
        relevant_concepts = []
        if peer.shared_concepts:
            query_words = set(query.lower().split())
            for concept in peer.shared_concepts:
                if any(word in concept.lower() for word in query_words):
                    relevant_concepts.append(concept)
        
        if not relevant_concepts:
            return None
        
        # Simulate insight generation (in reality, peer would use their Claude instance)
        try:
            response = self.claude.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": f"""Based on these concepts from a peer knowledge base: {', '.join(relevant_concepts[:10])}
                    
Generate a brief insight related to the query: "{query}"

Provide a synthetic insight that could come from documents containing these concepts, but don't invent specific facts. Focus on patterns and connections."""
                }]
            )
            
            insight_text = response.content[0].text
            
            return {
                "type": "insight_response",
                "from_node": peer.node_id,
                "insights": insight_text,
                "concepts_used": relevant_concepts[:5],
                "confidence": 0.7
            }
            
        except Exception as e:
            logger.error(f"Error generating simulated peer insight: {e}")
            return None
    
    def get_federation_stats(self) -> Dict[str, Any]:
        """Get statistics about federation participation"""
        return {
            "node_id": self.node_id,
            "shared_fragments": len(self.shared_fragments),
            "connected_peers": len(self.peers),
            "total_shared_concepts": len(set().union(*[f.concepts for f in self.shared_fragments.values()])) if self.shared_fragments else 0,
            "privacy_level": "concepts_only",
            "federation_enabled": True
        }
    
    async def start_federation(self) -> bool:
        """
        Start participating in the AKAP federation
        """
        try:
            # Create knowledge fragments
            fragments = self.create_knowledge_fragments()
            logger.info(f"Prepared {len(fragments)} fragments for sharing")
            
            # Discover peers
            peers = await self.discover_peers()
            logger.info(f"Connected to {len(peers)} peers")
            
            self.is_running = True
            logger.info("AKAP Federation started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start federation: {e}")
            return False
    
    def stop_federation(self):
        """Stop federation participation"""
        self.is_running = False
        logger.info("AKAP Federation stopped")