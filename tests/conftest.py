"""Pytest configuration and shared fixtures."""

import pytest
import asyncio
import sys
from pathlib import Path

# Add parent directory to path so we can import obsidian_mcp modules
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()