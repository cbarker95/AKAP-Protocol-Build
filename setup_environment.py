#!/usr/bin/env python3
"""
AKAP Protocol Environment Setup
Sets up the development environment and verifies Claude SDK connection
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def setup_environment():
    """Initialize the AKAP protocol development environment"""
    
    print("🚀 Setting up AKAP Protocol Development Environment")
    print("=" * 50)
    
    # Create necessary directories
    directories = [
        "data",
        "src/akap",
        "tests",
        "docs",
        "examples"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")
    
    # Check for .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("\n⚠️  .env file not found!")
        print("Please copy .env.template to .env and add your Claude API key:")
        print("cp .env.template .env")
        print("Then edit .env with your ANTHROPIC_API_KEY")
        return False
    
    # Load environment variables
    load_dotenv()
    
    # Verify Claude API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your_claude_api_key_here":
        print("\n❌ Claude API key not configured!")
        print("Please set ANTHROPIC_API_KEY in your .env file")
        return False
    
    print(f"✓ Claude API key configured: {api_key[:8]}...")
    
    # Test Claude SDK connection
    try:
        from anthropic import Anthropic
        
        client = Anthropic(api_key=api_key)
        
        # Simple test message
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=50,
            messages=[{
                "role": "user",
                "content": "Respond with 'AKAP Protocol SDK connection successful' if you can read this."
            }]
        )
        
        print(f"✓ Claude SDK test: {response.content[0].text}")
        
    except ImportError:
        print("❌ Anthropic SDK not installed. Run: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Claude SDK connection failed: {e}")
        return False
    
    # Verify Obsidian vault path
    vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "/Users/user/Documents/Obsidian Vault")
    if not Path(vault_path).exists():
        print(f"❌ Obsidian vault not found at: {vault_path}")
        print("Please update OBSIDIAN_VAULT_PATH in .env file")
        return False
    
    print(f"✓ Obsidian vault found: {vault_path}")
    
    print("\n🎉 Environment setup complete!")
    print("\nNext steps:")
    print("1. Run 'python examples/basic_knowledge_parsing.py' to test knowledge extraction")
    print("2. Explore the src/akap/ directory for core protocol components")
    
    return True

if __name__ == "__main__":
    success = setup_environment()
    sys.exit(0 if success else 1)