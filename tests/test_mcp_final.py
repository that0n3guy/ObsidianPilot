"""Final test to confirm search_by_date is available."""

import asyncio
from obsidianpilot.server import mcp

async def main():
    print("=== MCP Server Tools Check ===\n")
    
    # Get tools using the correct API
    tools_dict = await mcp.get_tools()
    
    print(f"Total tools registered: {len(tools_dict)}")
    print("\nAll tool names:")
    
    search_tool_found = False
    for tool_name in sorted(tools_dict.keys()):
        print(f"  - {tool_name}")
        if tool_name == "search_by_date_tool":
            search_tool_found = True
    
    if search_tool_found:
        print("\n✅ search_by_date_tool is registered and available!")
        tool_info = tools_dict["search_by_date_tool"]
        print(f"\nTool details:")
        print(f"  Type: {type(tool_info)}")
        
        # Show how to use it
        print("\n📝 Example usage in Claude Desktop:")
        print('  User: "Show me all notes I modified this week"')
        print('  User: "Find notes created in the last 30 days"')
        print('  User: "What notes were modified exactly 2 days ago?"')
    else:
        print("\n❌ search_by_date_tool not found!")

if __name__ == "__main__":
    asyncio.run(main())