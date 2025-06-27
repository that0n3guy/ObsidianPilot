# Release Notes - v1.1.6

## Fixed: Timeout Errors with Large Notes

This release fixes a critical issue where creating or updating large notes would report errors even though the operations succeeded.

### What was happening:
- When creating or updating notes with significant content, the server would timeout while trying to fetch the note immediately after the operation
- Users would see: `Error calling tool 'create_note_tool': 'str' object has no attribute 'message'`
- The note would actually be created/updated successfully, but the error message would cause AI assistants to retry the operation

### The fix:
- Added a small delay (0.5s) after create/update operations to give Obsidian time to process
- Implemented graceful timeout handling that returns a basic Note object when the fetch times out
- Operations now complete successfully without false error messages

### Impact:
- No more false errors when working with large notes
- AI assistants won't retry operations that already succeeded
- Better reliability for bulk operations and content generation

### Technical details:
- Modified `ObsidianAPI.create_note()` and `ObsidianAPI.update_note()` methods
- Added try-catch blocks for `httpx.ReadTimeout` and `httpx.ConnectError`
- Returns synthetic Note objects with basic metadata when fetching times out

This fix ensures smooth operation regardless of note size, making the server more reliable for AI-powered workflows.