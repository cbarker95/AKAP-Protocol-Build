"""
AKAP: Autonomous Knowledge & Agent Protocol
A protocol for knowledge sovereignty and collective intelligence
"""

__version__ = "0.1.0"
__author__ = "AKAP Protocol Contributors"
__description__ = "Knowledge sovereignty through AI-assisted collective intelligence"

from .knowledge_node import KnowledgeNode
from .semantic_processor import SemanticProcessor
from .pattern_extractor import PatternExtractor
from .federation_protocol import AKAPFederationProtocol
from .performance_optimizer import PerformanceOptimizer
from .web_dashboard import AKAPDashboard

__all__ = [
    "KnowledgeNode",
    "SemanticProcessor",
    "PatternExtractor",
    "AKAPFederationProtocol",
    "PerformanceOptimizer", 
    "AKAPDashboard"
]