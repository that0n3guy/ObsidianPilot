# Release v1.1.5 - Performance Optimization & Link Validity Fix

## 🚀 Major Performance Improvements

### Optimized Link Management Tools
Completely rewritten link management implementation with dramatic performance gains:

- **84x faster** link validity checking
- **96x faster** broken link detection
- **2x faster** backlink searches

### Key Optimizations
1. **Vault Index Caching**: Built-in 5-minute cache for vault structure
2. **Batch Processing**: Check multiple links in a single operation
3. **Parallel Scanning**: Process notes concurrently for faster results

### Performance Comparison
| Operation | v1.1.4 | v1.1.5 | Improvement |
|-----------|--------|--------|-------------|
| Check link validity (6 links) | 232ms | 3ms | **84x faster** |
| Find broken links (directory) | 17.9s | 187ms | **96x faster** |
| Get backlinks | 389ms | 208ms | **2x faster** |

## 🐛 Bug Fixes

### Fixed Link Validity Checking
- **Issue**: Link validity checking was incorrectly marking valid links as broken when notes were in different folders
- **Fix**: Now searches the entire vault to find notes by name, not just checking the exact path
- **Impact**: `get_outgoing_links` with `check_validity=true` now correctly identifies which links are valid

### Enhanced find_broken_links
- **New**: Added `single_note` parameter to check broken links in just one note
- **Benefit**: No need to scan the entire vault when you just want to check one note's links

## 📊 Example

For a note with links like `[[Apple TOC]]` where the actual note is at `Apple/Apple TOC.md`:

**Before (v1.1.4)**:
```json
{
  "path": "Apple TOC.md",
  "exists": false  // ❌ Incorrectly marked as broken
}
```

**After (v1.1.5)**:
```json
{
  "path": "Apple TOC.md",
  "exists": true,  // ✅ Correctly identified as valid
  "actual_path": "Apple/Apple TOC.md"  // Shows where it actually exists
}
```

## 🎯 Usage

Check links in a single note:
```python
# Check outgoing links with validity
result = await get_outgoing_links("Daily/2025-01-09.md", check_validity=True)

# Find broken links in just one note
result = await find_broken_links(single_note="Daily/2025-01-09.md")
```

## 🔧 Technical Details
- Maintains exact same API interface - no breaking changes
- Caching is automatic and transparent
- Cache expires after 5 minutes to balance performance with vault changes