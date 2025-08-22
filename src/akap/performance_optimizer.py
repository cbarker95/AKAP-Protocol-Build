"""
AKAP Performance Optimizer
Batch processing, memory management, and scaling optimizations for large knowledge bases
"""

import os
import gc
import logging
import time
import threading
from typing import Dict, List, Optional, Any, Iterator, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import psutil
from pathlib import Path
import pickle
from datetime import datetime, timedelta
import json
import asyncio
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Track performance metrics for optimization"""
    documents_processed: int = 0
    processing_time: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    embeddings_generated: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    batch_size: int = 0
    timestamp: str = ""

class PerformanceOptimizer:
    """
    Optimize AKAP performance for large knowledge bases
    
    Features:
    - Batch processing with configurable batch sizes
    - Memory management and garbage collection
    - Caching for expensive operations
    - Parallel processing for CPU-bound tasks
    - Progress tracking and performance metrics
    - Adaptive batch sizing based on system resources
    """
    
    def __init__(self, knowledge_node, max_workers: int = None, cache_dir: str = "./data/cache"):
        self.knowledge_node = knowledge_node
        self.max_workers = max_workers or min(4, os.cpu_count() or 1)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Performance tracking
        self.metrics = PerformanceMetrics()
        self.performance_history: List[PerformanceMetrics] = []
        
        # Batch processing configuration
        self.batch_size = self._calculate_optimal_batch_size()
        self.max_batch_size = 100
        self.min_batch_size = 5
        
        # Caching
        self.concept_cache: Dict[str, List[str]] = {}
        self.embedding_cache: Dict[str, np.ndarray] = {}
        
        # System monitoring
        self.monitor_thread = None
        self.is_monitoring = False
        
        logger.info(f"Performance optimizer initialized with {self.max_workers} workers, batch size {self.batch_size}")
    
    def _calculate_optimal_batch_size(self) -> int:
        """Calculate optimal batch size based on available system resources"""
        
        # Get system memory
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        
        # Get CPU count
        cpu_count = psutil.cpu_count()
        
        # Adaptive batch sizing
        if available_gb >= 8 and cpu_count >= 8:
            return 50  # High-end system
        elif available_gb >= 4 and cpu_count >= 4:
            return 25  # Mid-range system
        else:
            return 10  # Lower-end system
        
    def start_monitoring(self):
        """Start system resource monitoring"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_resources, daemon=True)
        self.monitor_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop system resource monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        logger.info("Performance monitoring stopped")
    
    def _monitor_resources(self):
        """Monitor system resources and adjust batch size accordingly"""
        while self.is_monitoring:
            try:
                # Monitor memory usage
                memory = psutil.virtual_memory()
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # Adaptive batch sizing based on resource usage
                if memory.percent > 80 or cpu_percent > 90:
                    # Reduce batch size if resources are stressed
                    self.batch_size = max(self.min_batch_size, int(self.batch_size * 0.8))
                elif memory.percent < 50 and cpu_percent < 50:
                    # Increase batch size if resources are available
                    self.batch_size = min(self.max_batch_size, int(self.batch_size * 1.2))
                
                self.metrics.memory_usage_mb = memory.used / (1024**2)
                self.metrics.cpu_usage_percent = cpu_percent
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                break
    
    def process_documents_batch(self, file_paths: List[Path], batch_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Process documents in optimized batches
        
        Args:
            file_paths: List of document file paths to process
            batch_size: Override default batch size
            
        Returns:
            Processing results and metrics
        """
        
        batch_size = batch_size or self.batch_size
        total_files = len(file_paths)
        
        logger.info(f"Processing {total_files} documents in batches of {batch_size}")
        
        start_time = time.time()
        processed_docs = {}
        errors = []
        
        # Process in batches
        for i in range(0, total_files, batch_size):
            batch_files = file_paths[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_files + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch_files)} files)")
            
            try:
                # Process batch with parallel workers
                batch_results = self._process_batch_parallel(batch_files)
                processed_docs.update(batch_results)
                
                # Memory management after each batch
                self._cleanup_memory()
                
                # Update metrics
                self.metrics.documents_processed += len(batch_files)
                
                # Progress callback
                progress = (i + len(batch_files)) / total_files
                logger.info(f"Progress: {progress:.1%} ({self.metrics.documents_processed}/{total_files})")
                
            except Exception as e:
                logger.error(f"Error processing batch {batch_num}: {e}")
                errors.append(f"Batch {batch_num}: {str(e)}")
                continue
        
        # Final metrics
        total_time = time.time() - start_time
        self.metrics.processing_time = total_time
        self.metrics.batch_size = batch_size
        self.metrics.timestamp = datetime.now().isoformat()
        
        # Store metrics history
        self.performance_history.append(self.metrics)
        
        results = {
            'processed_documents': processed_docs,
            'total_processed': len(processed_docs),
            'total_time': total_time,
            'documents_per_second': len(processed_docs) / total_time if total_time > 0 else 0,
            'errors': errors,
            'metrics': self.metrics
        }
        
        logger.info(f"Batch processing complete: {len(processed_docs)} documents in {total_time:.2f}s")
        return results
    
    def _process_batch_parallel(self, file_paths: List[Path]) -> Dict[str, Any]:
        """Process a batch of files using parallel workers"""
        
        results = {}
        
        # Use thread pool for I/O-bound document parsing
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all files in batch
            future_to_file = {
                executor.submit(self._process_single_document, file_path): file_path 
                for file_path in file_paths
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    doc = future.result()
                    if doc:
                        results[doc.title] = doc
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
        
        return results
    
    def _process_single_document(self, file_path: Path):
        """Process a single document with caching"""
        
        # Check cache first
        cache_key = f"{file_path.name}_{file_path.stat().st_mtime}"
        
        if cache_key in self.concept_cache:
            self.metrics.cache_hits += 1
            # Reconstruct document from cache
            cached_concepts = self.concept_cache[cache_key]
            # This is simplified - in practice would reconstruct full document
            return None
        
        self.metrics.cache_misses += 1
        
        # Parse document
        try:
            doc = self.knowledge_node.parse_document(file_path)
            if doc:
                # Cache concepts for future use
                self.concept_cache[cache_key] = doc.concepts
            return doc
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return None
    
    def generate_embeddings_batch(self, documents: Dict[str, Any], batch_size: Optional[int] = None) -> Dict[str, np.ndarray]:
        """
        Generate embeddings in optimized batches
        
        Args:
            documents: Dictionary of document_id -> document
            batch_size: Override default batch size for embeddings
            
        Returns:
            Dictionary of document_id -> embedding
        """
        
        if not self.knowledge_node.semantic_processor:
            logger.warning("Semantic processor not available for embeddings")
            return {}
        
        batch_size = batch_size or min(self.batch_size, 20)  # Smaller batches for embeddings
        doc_items = list(documents.items())
        total_docs = len(doc_items)
        
        logger.info(f"Generating embeddings for {total_docs} documents in batches of {batch_size}")
        
        start_time = time.time()
        embeddings = {}
        
        for i in range(0, total_docs, batch_size):
            batch_items = doc_items[i:i + batch_size]
            batch_texts = []
            batch_ids = []
            
            for doc_id, doc in batch_items:
                # Create combined text for embedding
                combined_text = f"{doc.title}\n\n{doc.content[:2000]}"  # Truncate for performance
                batch_texts.append(combined_text)
                batch_ids.append(doc_id)
            
            try:
                # Generate embeddings for batch
                batch_embeddings = self.knowledge_node.semantic_processor.embedding_model.encode(
                    batch_texts, 
                    show_progress_bar=False,
                    convert_to_numpy=True
                )
                
                # Store embeddings
                for doc_id, embedding in zip(batch_ids, batch_embeddings):
                    embeddings[doc_id] = embedding
                
                self.metrics.embeddings_generated += len(batch_items)
                
                # Progress update
                progress = (i + len(batch_items)) / total_docs
                logger.info(f"Embedding progress: {progress:.1%}")
                
                # Memory cleanup
                del batch_embeddings
                gc.collect()
                
            except Exception as e:
                logger.error(f"Error generating embeddings for batch: {e}")
                continue
        
        total_time = time.time() - start_time
        logger.info(f"Generated {len(embeddings)} embeddings in {total_time:.2f}s")
        
        return embeddings
    
    def _cleanup_memory(self):
        """Perform memory cleanup and garbage collection"""
        
        # Clear caches if they get too large
        if len(self.concept_cache) > 1000:
            # Keep only most recent 500 entries
            sorted_keys = sorted(self.concept_cache.keys())
            keys_to_remove = sorted_keys[:-500]
            for key in keys_to_remove:
                del self.concept_cache[key]
        
        # Force garbage collection
        gc.collect()
        
        # Log memory usage
        memory = psutil.virtual_memory()
        logger.debug(f"Memory cleanup: {memory.percent:.1f}% used")
    
    def save_cache(self):
        """Save caches to disk for persistence"""
        try:
            concept_cache_path = self.cache_dir / "concept_cache.pkl"
            with open(concept_cache_path, 'wb') as f:
                pickle.dump(self.concept_cache, f)
            
            logger.info(f"Cache saved to {concept_cache_path}")
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def load_cache(self):
        """Load caches from disk"""
        try:
            concept_cache_path = self.cache_dir / "concept_cache.pkl"
            if concept_cache_path.exists():
                with open(concept_cache_path, 'rb') as f:
                    self.concept_cache = pickle.load(f)
                logger.info(f"Cache loaded from {concept_cache_path}")
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        
        if not self.performance_history:
            return {"message": "No performance data available"}
        
        # Aggregate metrics
        total_docs = sum(m.documents_processed for m in self.performance_history)
        total_time = sum(m.processing_time for m in self.performance_history)
        avg_docs_per_second = total_docs / total_time if total_time > 0 else 0
        
        # Cache performance
        total_requests = self.metrics.cache_hits + self.metrics.cache_misses
        cache_hit_rate = self.metrics.cache_hits / total_requests if total_requests > 0 else 0
        
        # System resources
        memory = psutil.virtual_memory()
        cpu_count = psutil.cpu_count()
        
        report = {
            'performance_summary': {
                'total_documents_processed': total_docs,
                'total_processing_time': total_time,
                'average_documents_per_second': avg_docs_per_second,
                'current_batch_size': self.batch_size,
                'worker_threads': self.max_workers
            },
            'cache_performance': {
                'cache_hits': self.metrics.cache_hits,
                'cache_misses': self.metrics.cache_misses,
                'hit_rate': cache_hit_rate,
                'cache_size': len(self.concept_cache)
            },
            'system_resources': {
                'cpu_cores': cpu_count,
                'memory_total_gb': memory.total / (1024**3),
                'memory_available_gb': memory.available / (1024**3),
                'memory_usage_percent': memory.percent
            },
            'optimization_recommendations': self._get_optimization_recommendations()
        }
        
        return report
    
    def _get_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on performance data"""
        
        recommendations = []
        memory = psutil.virtual_memory()
        
        if memory.percent > 80:
            recommendations.append("Consider reducing batch size or adding more RAM")
        
        if self.metrics.cache_hits / (self.metrics.cache_hits + self.metrics.cache_misses) < 0.5:
            recommendations.append("Cache hit rate is low - consider increasing cache size")
        
        if len(self.performance_history) > 1:
            recent_perf = self.performance_history[-1]
            prev_perf = self.performance_history[-2] 
            
            if recent_perf.processing_time > prev_perf.processing_time * 1.2:
                recommendations.append("Processing time increasing - monitor for performance degradation")
        
        if not recommendations:
            recommendations.append("Performance is within normal parameters")
            
        return recommendations