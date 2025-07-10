# ObsidianPilot v2.1.3 Release Notes

## 🐛 Critical Bug Fix: Boolean Search with Multi-word Terms

### Overview
Version 2.1.3 fixes a critical bug in FTS5 boolean search where queries combining multi-word terms with OR operators would return zero results.

### 🎯 Issue Fixed
- **❌ Boolean OR with multi-word terms failed**: Queries like `Ahmed EL-Emawy OR "Medical Resource Staffing"` returned 0 results
- **✅ Now working**: Same query now returns all expected results from both terms

### 🔍 Root Cause
The FTS5 query transformation logic incorrectly converted boolean queries containing multi-word terms into phrase searches, breaking the boolean operators.

**Before (Broken)**:
- Input: `Ahmed EL-Emawy OR "Medical Resource Staffing"`
- Transformed: `"Ahmed EL-Emawy OR Medical Resource Staffing"` (entire query as phrase)
- Result: 0 results (searching for the entire string as one phrase)

**After (Fixed)**:
- Input: `Ahmed EL-Emawy OR "Medical Resource Staffing"`  
- Transformed: `"Ahmed EL-Emawy" OR "Medical Resource Staffing"` (proper boolean)
- Result: All results containing either term

### 🔧 Technical Details

#### Enhanced Query Transformation
- Added `_quote_multiword_terms()` method to properly handle multi-word terms in boolean queries
- Improved boolean operator detection to handle complex queries
- Multi-word terms are now automatically quoted when used with boolean operators

#### Examples of Fixed Queries
```
✅ Ahmed EL-Emawy OR "Medical Resource Staffing" 
✅ John Smith AND "Project Management"
✅ "Data Science" OR machine learning
✅ Peter Olson AND Tyler Chowdhry
```

### 🚀 Impact
This fix enables complex searches that were previously impossible:
- Searching for multiple people with multi-word names
- Combining company names with individual terms
- Complex boolean queries mixing quoted phrases and multi-word terms

### Backward Compatibility
- No breaking changes
- All existing queries continue to work as before
- Simple searches and single boolean operators unaffected

---

**Installation**: `pip install ObsidianPilot==2.1.3`

**Testing**: The problematic query `Ahmed EL-Emawy OR "Medical Resource Staffing"` should now return results from both terms.