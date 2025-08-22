# AKAP Protocol Setup Guide

## Quick Start

### Prerequisites

- Python 3.9+
- Anthropic API key (from [console.anthropic.com](https://console.anthropic.com))

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/AKAP-Protocol-Build.git
   cd AKAP-Protocol-Build
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.template .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

4. **Verify setup:**
   ```bash
   python setup_environment.py
   ```

### Basic Usage

```python
from akap import KnowledgeNode

# Initialize with your Obsidian vault
node = KnowledgeNode("/path/to/your/obsidian/vault")

# Build knowledge graph with semantic embeddings
node.build_knowledge_graph()

# Extract patterns and insights
patterns = node.extract_patterns()
insights = node.get_insights()

# Semantic search
results = node.semantic_search("AI-assisted product design")
```

## Features

### 🧠 Core Knowledge Processing
- **Document Parsing**: Obsidian markdown with `[[links]]` and frontmatter
- **Concept Extraction**: AI-powered key concept identification using Claude
- **Knowledge Graph**: NetworkX graph with documents and concept relationships

### 🔍 Semantic Search
- **Vector Embeddings**: sentence-transformers with 'all-MiniLM-L6-v2'
- **ChromaDB Storage**: Persistent vector database for similarity search
- **Hybrid Search**: Combines semantic similarity with keyword matching

### 🎨 Pattern Recognition
- **Theme Identification**: Cross-document themes with semantic clustering
- **Insight Generation**: Strategic insights using Claude 3.5 Sonnet
- **Gap Analysis**: Knowledge gap detection with expansion suggestions
- **Relationship Mapping**: Concept co-occurrence and relationship strength

## Examples

### Simple Test
```bash
python examples/simple_test.py
```
Tests basic functionality with a single document.

### Semantic Search Demo
```bash
python examples/semantic_search_demo.py
```
Demonstrates vector similarity search capabilities.

### Pattern Extraction Demo
```bash
python examples/pattern_extraction_demo.py
```
Full pattern recognition and insight generation showcase.

## Project Structure

```
AKAP-Protocol-Build/
├── src/akap/                  # Core protocol implementation
│   ├── knowledge_node.py      # Main knowledge processing class
│   ├── semantic_processor.py  # Vector search and ChromaDB integration
│   ├── pattern_extractor.py   # Cross-document pattern recognition
│   └── __init__.py            # Package exports
├── examples/                  # Usage examples and demos
├── tests/                     # Test suite (coming soon)
├── docs/                      # Documentation (coming soon)
├── data/                      # Local data storage (gitignored)
├── requirements.txt           # Python dependencies
├── setup_environment.py      # Environment setup and verification
├── .env.template             # Environment variable template
└── README.md                 # Project overview
```

## Configuration

### Environment Variables

- `ANTHROPIC_API_KEY`: Your Claude API key (**required**)
- `OBSIDIAN_VAULT_PATH`: Path to your Obsidian vault (default: `/Users/user/Documents/Obsidian Vault`)
- `CHROMA_PERSIST_DIRECTORY`: ChromaDB storage location (default: `./data/vector_db`)
- `DEBUG`: Enable debug logging (default: `True`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

### Performance Tuning

For large vaults (100+ documents), consider:
- Processing documents in batches
- Using faster embedding models
- Adjusting ChromaDB collection settings
- Implementing document filtering

## API Reference

### KnowledgeNode

Main class for knowledge processing.

#### Methods

- `build_knowledge_graph()`: Parse documents and build graph
- `semantic_search(query, top_k=5)`: Vector similarity search
- `extract_patterns()`: Full pattern analysis
- `get_insights(max_insights=5)`: Generate strategic insights
- `find_knowledge_gaps()`: Identify knowledge gaps
- `get_themes()`: Extract cross-document themes

### SemanticProcessor

Vector similarity search and ChromaDB integration.

#### Methods

- `embed_documents(documents)`: Generate and store embeddings
- `semantic_search(query, top_k=5)`: Search by vector similarity
- `get_similar_documents(doc_id, top_k=5)`: Find similar documents

### PatternExtractor

Cross-document pattern recognition and insight generation.

#### Methods

- `extract_document_themes()`: Identify major themes
- `analyze_concept_relationships()`: Map concept co-occurrences
- `find_knowledge_gaps()`: Detect expansion opportunities
- `generate_insights(max_insights=5)`: AI-powered insights

## Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
black src/ examples/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Troubleshooting

### Common Issues

**"No module named 'akap'"**
- Ensure you're in the project directory
- Run `pip install -e .` for development installation

**"ChromaDB connection failed"**
- Check disk space in data directory
- Verify Python version compatibility
- Clear `./data/vector_db` and rebuild

**"Claude API key not working"**
- Verify key in .env file
- Check API key permissions at console.anthropic.com
- Ensure sufficient API credits

**"Slow processing for large vaults"**
- Process documents in smaller batches
- Consider using lighter embedding models
- Implement document filtering by modification date

### Performance Optimization

For production use:
- Use GPU acceleration for embeddings
- Implement document chunking for large files
- Add caching for frequently accessed patterns
- Consider distributed processing for very large vaults

## License

[To be determined]

## Roadmap

### ✅ Phase 1: Foundation
- [x] Basic knowledge parsing
- [x] Concept extraction with Claude
- [x] Simple graph building
- [x] Basic querying

### ✅ Phase 2: Enhanced Querying
- [x] Vector similarity search with ChromaDB
- [x] Improved relevance ranking
- [x] Semantic clustering

### ✅ Phase 3: Pattern Recognition
- [x] Cross-document pattern extraction
- [x] Insight generation
- [x] Knowledge evolution tracking

### 🔄 Phase 4: Federation (In Progress)
- [ ] P2P knowledge sharing protocols
- [ ] Decentralized coordination
- [ ] Collective intelligence emergence

## Support

For issues and questions:
- Check the troubleshooting section above
- Review example scripts for usage patterns
- Open an issue on GitHub with detailed error information
- Include relevant logs and configuration details