# Release Notes - v1.1.9

## Bug Fixes

### Fixed Package Installation Issues
- Renamed internal package structure from `src` to `obsidian_mcp` to follow Python packaging conventions
- Fixed import errors when package is installed via pip outside of development environment
- Updated entry point in pyproject.toml to use correct module path
- Updated all test imports to use the new package name

## Technical Details
- Changed entry point from `src.server:main` to `obsidian_mcp.server:main`
- Updated MANIFEST.in to reference the correct directory structure
- No changes to external API or command-line interface - `uvx obsidian-mcp` continues to work as before

## Compatibility
- No breaking changes - all existing configurations and integrations continue to work
- The package name `obsidian-mcp` and command-line interface remain unchanged