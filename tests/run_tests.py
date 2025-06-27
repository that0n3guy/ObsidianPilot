#!/usr/bin/env python
"""Simple test runner for Obsidian MCP server.

Run all tests without requiring pytest:
    python tests/run_tests.py

Run specific test type:
    python tests/run_tests.py unit
    python tests/run_tests.py integration  
    python tests/run_tests.py live
"""

import sys
import subprocess
from pathlib import Path


def run_unit_tests():
    """Run unit tests with or without pytest."""
    print("\n" + "="*60)
    print("Running Unit Tests")
    print("="*60)
    
    try:
        # Try with pytest first
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_unit.py", "-v"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(result.stdout)
            return True
        elif "No module named 'pytest'" in result.stderr:
            print("⚠️  pytest not installed - skipping unit tests")
            print("Install with: pip install pytest pytest-asyncio")
            return None
        else:
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"Error running unit tests: {e}")
        return False


def run_integration_tests():
    """Run integration tests."""
    print("\n" + "="*60)
    print("Running Integration Tests")
    print("="*60)
    
    try:
        # Try with pytest
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_integration.py", "-v"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(result.stdout)
            return True
        elif "No module named 'pytest'" in result.stderr:
            print("⚠️  pytest not installed - skipping integration tests")
            return None
        else:
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"Error running integration tests: {e}")
        return False


def run_live_tests():
    """Run live tests with real Obsidian."""
    print("\n" + "="*60)
    print("Running Live Tests (Requires Obsidian)")
    print("="*60)
    
    try:
        result = subprocess.run(
            [sys.executable, "tests/test_live.py"],
            check=False
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error running live tests: {e}")
        return False


def main():
    """Run all or specific tests."""
    import os
    
    # Ensure we're in the right directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Determine which tests to run
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        if test_type == "unit":
            success = run_unit_tests()
        elif test_type == "integration":
            success = run_integration_tests()
        elif test_type == "live":
            success = run_live_tests()
        else:
            print(f"Unknown test type: {test_type}")
            print("Valid options: unit, integration, live")
            return 1
            
        return 0 if success else 1
    
    # Run all tests
    print("Obsidian MCP Server - Test Suite")
    print("================================\n")
    
    results = []
    
    # Unit tests
    unit_result = run_unit_tests()
    if unit_result is not None:
        results.append(("Unit Tests", unit_result))
    
    # Integration tests
    int_result = run_integration_tests()
    if int_result is not None:
        results.append(("Integration Tests", int_result))
    
    # Live tests (only if API key is set)
    if os.getenv("OBSIDIAN_REST_API_KEY"):
        results.append(("Live Tests", run_live_tests()))
    else:
        print("\n⚠️  Skipping live tests - OBSIDIAN_REST_API_KEY not set")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    failed = sum(1 for _, passed in results if not passed)
    total = len(results)
    
    print(f"\nTotal: {total - failed}/{total} passed")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())