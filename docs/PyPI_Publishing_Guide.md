# PyPI Publishing Guide for Obsidian MCP

This guide walks through the process of publishing the Obsidian MCP package to PyPI (Python Package Index).

## Prerequisites

- Python 3.10+ installed
- A built package ready for distribution
- Admin access to the project repository

## Step 1: Create PyPI Account

1. Go to https://pypi.org/account/register/
2. Create an account and verify your email
3. Enable 2FA (required for publishing)

## Step 2: Create API Token

1. Go to https://pypi.org/manage/account/token/
2. Create a new API token with "Entire account" scope
3. Save this token securely - you'll only see it once!

## Step 3: Install Publishing Tools

```bash
pip install twine build
```

## Step 4: Clean and Build

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build the package
python -m build
```

## Step 5: Upload to Test PyPI (Optional but Recommended)

First test on TestPyPI to make sure everything works:

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# When prompted:
# Username: __token__
# Password: <your-test-pypi-token>
```

Test the installation:
```bash
uvx --index-url https://test.pypi.org/simple/ obsidian-mcp
```

## Step 6: Upload to PyPI

```bash
# Upload to real PyPI
twine upload dist/*

# When prompted:
# Username: __token__  
# Password: <your-pypi-token>
```

## Step 7: Configure .pypirc (Optional)

To avoid entering credentials each time, create `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-<your-token-here>

[testpypi]
username = __token__
password = pypi-<your-test-token-here>
```

Then you can just run:
```bash
twine upload dist/*
```

## Step 8: Verify Installation

Once uploaded, wait a minute or two, then test:

```bash
uvx obsidian-mcp
```

## Important Notes

1. **Package Name**: Your package name `obsidian-mcp` must be unique on PyPI
2. **Version**: Each upload must have a unique version number
3. **Cannot Delete**: You cannot truly delete packages from PyPI (only yank them)
4. **Email**: Your email will be public in the package metadata

## Pre-Upload Checklist

- [ ] Version number in `pyproject.toml` is correct
- [ ] README.md renders correctly (check with `twine check dist/*`)
- [ ] All tests pass
- [ ] No sensitive information in code
- [ ] LICENSE file included
- [ ] Package name is available on PyPI

## Checking Package Name Availability

```bash
pip install obsidian-mcp
# If it returns "ERROR: No matching distribution found"
# then the name is available
```

## Version Management

Before each release:

1. Update version in `pyproject.toml`
2. Update version in `src/server.py` (if hardcoded)
3. Create a git tag:
   ```bash
   git tag -a v1.1.0 -m "Release version 1.1.0"
   git push origin v1.1.0
   ```

## Troubleshooting

### "Invalid or non-existent authentication"
- Make sure you're using `__token__` as username
- Password should be your full token including the `pypi-` prefix

### "File already exists"
- You cannot upload the same version twice
- Increment the version number in `pyproject.toml`
- Rebuild with `python -m build`

### Package not installing with uvx
- Wait 1-2 minutes after upload for PyPI CDN to update
- Try clearing uvx cache if needed