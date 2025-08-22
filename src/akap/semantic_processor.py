"""
AKAP Semantic Processor
Enhanced querying with vector similarity search using ChromaDB
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SemanticProcessor:
    """
    Enhanced semantic processing using vector embeddings and ChromaDB
    
    Provides:
    - Document embedding generation
    - Vector similarity search
    - Semantic clustering
    - Improved relevance ranking
    """
    
    def __init__(self, persist_directory: Optional[str] = None):
        """Initialize the semantic processor with ChromaDB and embedding model"""
        
        # Set up ChromaDB
        self.persist_directory = persist_directory or os.getenv(
            "CHROMA_PERSIST_DIRECTORY", 
            "./data/vector_db"
        )
        
        # Ensure directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False
            )
        )
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="akap_knowledge",
            metadata={"description": "AKAP Protocol knowledge embeddings"}
        )
        
        # Initialize sentence transformer
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        logger.info(f"Initialized SemanticProcessor with {self.collection.count()} existing embeddings")
    
    def embed_documents(self, documents: Dict[str, Any]) -> None:
        """
        Generate and store embeddings for documents
        
        Args:
            documents: Dict of {doc_id: KnowledgeDocument}
        """
        
        # Prepare data for embedding
        doc_ids = []
        texts = []
        metadatas = []
        
        for doc_id, doc in documents.items():
            # Create a combined text for embedding
            combined_text = f"{doc.title}\n\n{doc.content}"
            if doc.concepts:
                combined_text += f"\n\nKey concepts: {', '.join(doc.concepts)}"
            
            doc_ids.append(doc_id)
            texts.append(combined_text)
            metadatas.append({
                "title": doc.title,
                "path": doc.path,
                "content_length": len(doc.content),
                "num_concepts": len(doc.concepts),
                "num_links": len(doc.links),
                "concepts": ", ".join(doc.concepts) if doc.concepts else ""
            })
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} documents...")
        embeddings = self.embedding_model.encode(texts).tolist()
        
        # Store in ChromaDB (upsert to handle updates)
        self.collection.upsert(
            ids=doc_ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        
        logger.info(f"Stored {len(embeddings)} document embeddings")
    
    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform semantic search using vector similarity
        
        Args:
            query: Natural language query
            top_k: Number of top results to return
            
        Returns:
            List of search results with metadata and scores
        """
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()[0]
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        search_results = []
        if results['ids'] and results['ids'][0]:  # Check if we have results
            for i, doc_id in enumerate(results['ids'][0]):
                search_results.append({
                    'id': doc_id,
                    'title': results['metadatas'][0][i]['title'],
                    'path': results['metadatas'][0][i]['path'],
                    'content': results['documents'][0][i],
                    'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                    'metadata': results['metadatas'][0][i]
                })
        
        logger.info(f"Semantic search for '{query}' returned {len(search_results)} results")
        return search_results
    
    def get_similar_documents(self, doc_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find documents similar to a given document
        
        Args:
            doc_id: ID of the reference document
            top_k: Number of similar documents to return
            
        Returns:
            List of similar documents with similarity scores
        """
        
        # Get the document embedding
        doc_result = self.collection.get(
            ids=[doc_id],
            include=["embeddings"]
        )
        
        if doc_result['embeddings'] is None or len(doc_result['embeddings']) == 0:
            logger.warning(f"No embedding found for document {doc_id}")
            return []
        
        doc_embedding = doc_result['embeddings'][0]
        
        # Search for similar documents
        results = self.collection.query(
            query_embeddings=[doc_embedding],
            n_results=top_k + 1,  # +1 because the document itself will be included
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results (excluding the original document)
        similar_docs = []
        if results['ids'] and results['ids'][0]:
            for i, result_id in enumerate(results['ids'][0]):
                if result_id != doc_id:  # Exclude the original document
                    similar_docs.append({
                        'id': result_id,
                        'title': results['metadatas'][0][i]['title'],
                        'path': results['metadatas'][0][i]['path'],
                        'similarity_score': 1 - results['distances'][0][i],
                        'metadata': results['metadatas'][0][i]
                    })
                
                if len(similar_docs) >= top_k:
                    break
        
        return similar_docs
    
    def get_concept_clusters(self, min_similarity: float = 0.7) -> Dict[str, List[str]]:
        """
        Identify clusters of similar documents based on embeddings
        
        Args:
            min_similarity: Minimum similarity threshold for clustering
            
        Returns:
            Dict of {cluster_name: [doc_ids]}
        """
        
        # Get all documents
        all_docs = self.collection.get(include=["metadatas"])
        
        clusters = {}
        processed_docs = set()
        
        for i, doc_id in enumerate(all_docs['ids']):
            if doc_id in processed_docs:
                continue
            
            # Find similar documents
            similar_docs = self.get_similar_documents(doc_id, top_k=20)
            
            # Create cluster with documents above similarity threshold
            cluster_docs = [doc_id]
            for similar_doc in similar_docs:
                if similar_doc['similarity_score'] >= min_similarity:
                    cluster_docs.append(similar_doc['id'])
                    processed_docs.add(similar_doc['id'])
            
            if len(cluster_docs) > 1:
                # Use the title of the first document as cluster name
                cluster_name = all_docs['metadatas'][i]['title']
                clusters[cluster_name] = cluster_docs
            
            processed_docs.add(doc_id)
        
        logger.info(f"Identified {len(clusters)} concept clusters")
        return clusters
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the semantic processor"""
        
        count = self.collection.count()
        
        return {
            "total_embeddings": count,
            "embedding_model": "all-MiniLM-L6-v2",
            "vector_database": "ChromaDB",
            "persist_directory": self.persist_directory
        }