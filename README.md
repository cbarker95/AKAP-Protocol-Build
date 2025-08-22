# AKAP Protocol

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Autonomous Knowledge & Agent Protocol**  
*Knowledge sovereignty through AI-assisted collective intelligence*

## Overview

AKAP Protocol is a system for parsing, understanding, and querying personal knowledge bases while maintaining privacy and sovereignty. Built with the Claude SDK, it enables semantic processing of Obsidian vaults and other markdown-based knowledge systems.

## Features

- 📊 **Knowledge Graph Building**: Parse markdown files and build NetworkX knowledge graphs
- 🧠 **AI-Powered Concept Extraction**: Use Claude to identify key concepts and relationships
- 🔍 **Semantic Querying**: Query your knowledge base using natural language
- 🔗 **Obsidian Integration**: Full support for `[[links]]` and frontmatter
- 🛡️ **Privacy-First**: All processing happens locally with your own API keys

## Quick Start

### Prerequisites

- Python 3.9+
- Anthropic API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd AKAP-Protocol-Build
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.template .env
# Edit .env with your ANTHROPIC_API_KEY
```

4. Run setup verification:
```bash
python setup_environment.py
```

### Basic Usage

```python
from akap import KnowledgeNode

# Initialize with your vault path
node = KnowledgeNode("/path/to/your/vault")

# Build knowledge graph
node.build_knowledge_graph()

# Query your knowledge
response = node.query_knowledge("What is the AKAP protocol?")
print(response)
```

## Examples

- `examples/simple_test.py` - Basic functionality test
- `examples/basic_knowledge_parsing.py` - Full vault processing demo

## Project Structure

```
AKAP-Protocol-Build/
├── src/akap/              # Core protocol implementation
│   ├── knowledge_node.py  # Main knowledge processing class
│   └── __init__.py        # Package exports
├── examples/              # Usage examples and demos
├── tests/                 # Test suite (coming soon)
├── docs/                  # Documentation (coming soon)
├── data/                  # Local data storage (gitignored)
└── requirements.txt       # Python dependencies
```

## Roadmap

### Phase 1: Foundation ✅
- [x] Basic knowledge parsing
- [x] Concept extraction with Claude
- [x] Simple graph building
- [x] Basic querying

### Phase 2: Enhanced Querying (In Progress)
- [ ] Vector similarity search with ChromaDB
- [ ] Improved relevance ranking
- [ ] Semantic clustering

### Phase 3: Pattern Recognition
- [ ] Cross-document pattern extraction
- [ ] Insight generation
- [ ] Knowledge evolution tracking

### Phase 4: Federation
- [ ] P2P knowledge sharing protocols
- [ ] Decentralized coordination
- [ ] Collective intelligence emergence

## Contributing

This project is in early development. Contributions welcome!

## License

[To be determined]

## Vision

AKAP Protocol is part of a larger vision for post-scarcity economics and knowledge sovereignty. By enabling individuals to better understand and leverage their own knowledge while preserving privacy, we aim to support the transition to more collaborative and abundant economic models.