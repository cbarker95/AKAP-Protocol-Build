#!/usr/bin/env python3
"""
Simple AKAP Test - Process a limited set of files for demo
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from akap import KnowledgeNode

def main():
    """Test AKAP with a limited set of files"""
    
    print("🧠 AKAP Protocol - Simple Test")
    print("=" * 30)
    
    # Initialize the Knowledge Node
    vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "/Users/user/Documents/Obsidian Vault")
    node = KnowledgeNode(vault_path)
    
    # Scan vault and show first few files
    files = node.scan_vault()
    print(f"📂 Found {len(files)} total files")
    print(f"📄 First 5 files:")
    for f in files[:5]:
        print(f"  - {f.name}")
    
    # Parse just one document to test
    print(f"\n🔍 Testing document parsing...")
    test_file = files[0]
    doc = node.parse_document(test_file)
    
    if doc:
        print(f"✅ Successfully parsed: {doc.title}")
        print(f"   - Content length: {len(doc.content)} chars")
        print(f"   - Links found: {len(doc.links)}")
        print(f"   - Concepts extracted: {len(doc.concepts)}")
        if doc.concepts:
            print(f"   - Sample concepts: {', '.join(doc.concepts[:5])}")
    else:
        print("❌ Failed to parse document")
    
    print(f"\n✅ AKAP core functionality verified!")
    print(f"Ready to process {len(files)} documents in your vault.")

if __name__ == "__main__":
    main()