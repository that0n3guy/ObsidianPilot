#!/usr/bin/env python3
"""Quick test to verify the MCP server can start and connect to Obsidian."""

import os
import sys
import subprocess
import asyncio

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_environment():
    """Test environment setup."""
    print("1. Testing environment...")
    
    # Check Python version
    print(f"   Python version: {sys.version}")
    if sys.version_info < (3, 10):
        print("   ❌ Python 3.10+ required")
        return False
    print("   ✅ Python version OK")
    
    # Check API key
    api_key = os.getenv("OBSIDIAN_REST_API_KEY")
    if not api_key:
        print("   ❌ OBSIDIAN_REST_API_KEY not found")
        return False
    print(f"   ✅ API key found (length: {len(api_key)})")
    
    return True

def test_imports():
    """Test that all modules can be imported."""
    print("\n2. Testing imports...")
    try:
        import obsidianpilot.server
        print("   ✅ src.server imports successfully")
        
        from obsidianpilot.utils import ObsidianAPI
        print("   ✅ ObsidianAPI imports successfully")
        
        from obsidianpilot.tools import read_note, create_note
        print("   ✅ Tool imports successful")
        
        return True
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False

async def test_obsidian_connection():
    """Test connection to Obsidian REST API."""
    print("\n3. Testing Obsidian connection...")
    try:
        from obsidianpilot.utils import ObsidianAPI
        api = ObsidianAPI()
        
        # Try to get vault structure
        vault = await api.get_vault_structure()
        print(f"   ✅ Connected to Obsidian vault")
        print(f"   Found {len(vault)} items in vault root")
        
        return True
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False

def test_server_startup():
    """Test that the server can start."""
    print("\n4. Testing server startup...")
    try:
        # Try to start the server with a timeout
        process = subprocess.Popen(
            [sys.executable, "-m", "src.server"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,  # Provide stdin to prevent immediate exit
            text=True
        )
        
        # Wait a bit to see if it starts
        import time
        time.sleep(1)
        
        # Check if we got the expected startup message
        if process.poll() is None:
            # Still running, that's good
            process.terminate()
            process.wait()
            stdout, stderr = process.communicate()
        else:
            # Process ended, check why
            stdout, stderr = process.communicate()
        
        # Check for the expected startup message
        if "Starting MCP server 'obsidian-mcp'" in stderr:
            print("   ✅ Server starts successfully")
            print("   Server output confirms MCP initialization")
            return True
        else:
            print(f"   ❌ Unexpected output: {stderr}")
            return False
        
    except Exception as e:
        print(f"   ❌ Failed to start server: {e}")
        return False

async def main():
    """Run all tests."""
    print("Testing Obsidian MCP Server Local Setup")
    print("=" * 40)
    
    all_passed = True
    
    # Test environment
    if not test_environment():
        all_passed = False
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test Obsidian connection
    if not await test_obsidian_connection():
        all_passed = False
    
    # Test server startup
    if not test_server_startup():
        all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("✅ All tests passed! The server should work in Claude Desktop.")
        print("\nNext steps:")
        print("1. Restart Claude Desktop")
        print("2. Look for 'obsidian-dev' in the MCP servers list")
        print("3. If there are issues, check the logs in Claude Desktop")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print("\nTroubleshooting:")
        print("- Make sure Obsidian is running with REST API enabled")
        print("- Verify OBSIDIAN_REST_API_KEY is in your shell environment")
        print("- Check that Python 3.10+ is installed")
    
    print("\nClaude Desktop config location:")
    print("~/Library/Application Support/Claude/claude_desktop_config.json")

if __name__ == "__main__":
    asyncio.run(main())