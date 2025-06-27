# Release Notes - v1.1.7

## Changed: Default to HTTP Endpoint for Easier Setup

This release changes the default API endpoint from HTTPS to HTTP for better out-of-the-box compatibility.

### What changed:
- Default API endpoint is now `http://127.0.0.1:27123` (previously `https://localhost:27124`)
- This matches the default configuration of the Obsidian Local REST API plugin
- Users no longer need to configure the HTTPS endpoint or deal with self-signed certificate warnings

### Why this change:
- Many users were experiencing connection issues with the HTTPS endpoint
- The HTTP endpoint works by default without additional configuration
- The connection remains secure as it's localhost-only
- HTTPS is still fully supported for users who prefer it

### Impact:
- **New users**: Will have a working setup immediately after installation
- **Existing users**: No changes needed - your existing configuration will continue to work
- **HTTPS users**: Can still use HTTPS by setting `OBSIDIAN_API_URL="https://localhost:27124"`

### Documentation updates:
- README now shows HTTP as the default with HTTPS as an optional configuration
- Added notes about trailing slashes being handled automatically
- Updated troubleshooting section to mention both ports

This change improves the first-time user experience while maintaining full backward compatibility.