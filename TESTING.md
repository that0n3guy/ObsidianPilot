# Testing Guide for Obsidian MCP Server

This guide explains the testing structure and how to run tests for the Obsidian MCP server.

## Quick Start

```bash
# Run all tests (pytest optional)
python tests/run_tests.py

# Run only live tests (requires Obsidian)
export OBSIDIAN_REST_API_KEY="your-api-key"
python tests/test_live.py
```

## Test Structure

### Unit Tests (`tests/test_unit.py`)
Consolidated unit tests for all tools:
- Note management (CRUD operations)
- Search and discovery
- Organization tools
- Uses mocks, no Obsidian required
- Requires pytest

### Integration Tests (`tests/test_integration.py`)
Tests MCP server integration:
- Tool registration
- Error handling
- Full request/response flow
- Uses mocks, no Obsidian required
- Requires pytest

### Live Tests (`tests/test_live.py`)
Tests with real Obsidian REST API:
- Connection testing
- Complete workflow test
- Batch operations
- Requires Obsidian running
- No pytest needed

### Test Runner (`tests/run_tests.py`)
Smart test runner that:
- Detects if pytest is installed
- Runs appropriate tests
- Provides clear output
- Works without pytest for live tests

## Testing Checklist

Before releasing or deploying:

- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Manual tests connect to Obsidian successfully
- [ ] Create, read, update, delete operations work
- [ ] Search returns expected results
- [ ] Tag operations modify frontmatter correctly
- [ ] Error cases return helpful messages
- [ ] MCP Inspector can call all tools

## Running Tests

### Without pytest
```bash
# Just run live tests
python tests/test_live.py
```

### With pytest
```bash
# Run all tests
python tests/run_tests.py

# Run specific test file
pytest tests/test_unit.py -v

# Run specific test class
pytest tests/test_unit.py::TestNoteManagement -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### MCP Inspector Testing
See `docs/MCP_INSPECTOR_EXAMPLES.md` for interactive testing examples.

## Troubleshooting Tests

### "Connection refused" in manual tests
- Ensure Obsidian is running
- Check Local REST API plugin is enabled
- Verify API key is correct
- Check the port (default: 27124)

### Tests fail with "Module not found"
```bash
# Make sure you're in the project root
cd /path/to/obsidian-mcp

# Install in development mode
pip install -e .
```

### Mock tests pass but manual tests fail
- Check Obsidian REST API is accessible
- Verify your vault has the expected structure
- Check file permissions in your vault

## Writing New Tests

When adding new features:

1. **Add unit tests** to `tests/test_unit.py` in the appropriate class
2. **Update integration tests** if adding new tools
3. **Add live test scenarios** to `tests/test_live.py` if needed
4. **Update MCP Inspector examples** in `docs/MCP_INSPECTOR_EXAMPLES.md`

Example locations:
- Note CRUD operations → `TestNoteManagement` class
- Search/list functions → `TestSearchDiscovery` class  
- Tag/organization tools → `TestOrganization` class