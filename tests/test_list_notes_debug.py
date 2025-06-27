"""Debug script to investigate why list_notes doesn't return notes when called without a directory."""

import asyncio
import os
import sys
import json
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from obsidianpilot.utils import ObsidianAPI
from obsidianpilot.models import VaultItem
from obsidianpilot.tools.search_discovery import list_notes


async def debug_vault_structure():
    """Debug the vault structure and list_notes behavior."""
    print("=== DEBUGGING list_notes ISSUE ===\n")
    
    api = ObsidianAPI()
    
    # 1. Test raw API response for root
    print("1. Testing raw API response for root vault structure:")
    print("-" * 50)
    
    try:
        # Make raw API call
        response = await api._request("GET", "/vault/")
        raw_data = response.json()
        
        print(f"Raw API response type: {type(raw_data)}")
        print(f"Raw API response keys: {list(raw_data.keys()) if isinstance(raw_data, dict) else 'N/A'}")
        
        if isinstance(raw_data, dict) and "files" in raw_data:
            files = raw_data["files"]
            print(f"Number of items in 'files': {len(files)}")
            print(f"First 5 items: {json.dumps(files[:5], indent=2)}")
        else:
            print(f"Raw response: {json.dumps(raw_data[:5] if isinstance(raw_data, list) else raw_data, indent=2)}")
            
    except Exception as e:
        print(f"Error getting raw API response: {e}")
    
    print("\n")
    
    # 2. Test parsed vault items
    print("2. Testing parsed vault items from get_vault_structure():")
    print("-" * 50)
    
    try:
        vault_items = await api.get_vault_structure()
        print(f"Number of vault items: {len(vault_items)}")
        
        # Analyze item types
        folders = [item for item in vault_items if item.is_folder]
        files = [item for item in vault_items if not item.is_folder]
        md_files = [item for item in files if item.path.endswith('.md')]
        
        print(f"Folders: {len(folders)}")
        print(f"Files: {len(files)}")
        print(f"Markdown files: {len(md_files)}")
        
        print("\nFirst 5 folders:")
        for folder in folders[:5]:
            print(f"  - {folder.path}/ (is_folder={folder.is_folder}, children={folder.children})")
            
        print("\nFirst 5 markdown files:")
        for file in md_files[:5]:
            print(f"  - {file.path} (is_folder={file.is_folder})")
            
    except Exception as e:
        print(f"Error getting vault structure: {e}")
    
    print("\n")
    
    # 3. Test list_notes function
    print("3. Testing list_notes() function:")
    print("-" * 50)
    
    try:
        result = await list_notes(directory=None, recursive=True)
        print(f"list_notes result keys: {list(result.keys())}")
        print(f"Directory: {result.get('directory')}")
        print(f"Recursive: {result.get('recursive')}")
        print(f"Count: {result.get('count')}")
        print(f"Number of notes: {len(result.get('notes', []))}")
        
        if result.get('notes'):
            print("\nFirst 5 notes:")
            for note in result['notes'][:5]:
                print(f"  - {note}")
                
    except Exception as e:
        print(f"Error calling list_notes: {e}")
    
    print("\n")
    
    # 4. Debug the processing logic
    print("4. Debugging the processing logic in list_notes:")
    print("-" * 50)
    
    try:
        vault_items = await api.get_vault_structure()
        notes = []
        folders = set()
        
        def debug_process_item(item: VaultItem, parent_path: str = "", indent: int = 0):
            """Process item with debug output."""
            prefix = "  " * indent
            full_path = item.path
            
            print(f"{prefix}Processing: {item.path} (is_folder={item.is_folder}, name={item.name})")
            
            if item.is_folder:
                folders.add(full_path)
                print(f"{prefix}  -> Added to folders")
                
                # Check if children exist
                if item.children is not None:
                    print(f"{prefix}  -> Has {len(item.children)} children")
                    for child in item.children:
                        debug_process_item(child, item.path, indent + 1)
                else:
                    print(f"{prefix}  -> No children (children=None)")
                    
            elif full_path.endswith('.md'):
                notes.append({
                    "path": full_path,
                    "name": item.name
                })
                print(f"{prefix}  -> Added to notes as markdown file")
            else:
                print(f"{prefix}  -> Skipped (not a folder or .md file)")
        
        print("Processing vault items:")
        for i, item in enumerate(vault_items[:10]):  # Process first 10 items
            print(f"\nItem {i+1}:")
            debug_process_item(item)
            
        print(f"\nTotal notes found: {len(notes)}")
        print(f"Total folders found: {len(folders)}")
        
    except Exception as e:
        print(f"Error in debug processing: {e}")
    
    print("\n")
    
    # 5. Test specific directory
    print("5. Testing with a specific directory (if folders exist):")
    print("-" * 50)
    
    try:
        vault_items = await api.get_vault_structure()
        folders = [item for item in vault_items if item.is_folder]
        
        if folders:
            test_folder = folders[0].path
            print(f"Testing with directory: {test_folder}")
            
            # Test API response for specific directory
            folder_items = await api.get_vault_structure(test_folder)
            print(f"Items in {test_folder}: {len(folder_items)}")
            
            for item in folder_items[:5]:
                print(f"  - {item.path} (is_folder={item.is_folder})")
                
            # Test list_notes with directory
            result = await list_notes(directory=test_folder, recursive=True)
            print(f"\nlist_notes for {test_folder}:")
            print(f"  Count: {result.get('count')}")
            print(f"  Notes: {len(result.get('notes', []))}")
            
        else:
            print("No folders found in vault root")
            
    except Exception as e:
        print(f"Error testing specific directory: {e}")
    
    print("\n")
    
    # 6. Identify the issue
    print("6. ISSUE IDENTIFICATION:")
    print("-" * 50)
    print("The issue appears to be that when getting the vault structure for root,")
    print("the API returns items but folders don't have their children populated.")
    print("The recursive processing in list_notes relies on item.children being populated,")
    print("but this is always None for items returned from the root vault structure.")
    print("\nPossible solutions:")
    print("1. Make separate API calls for each folder to get its contents")
    print("2. Use a different API endpoint that returns the full tree structure")
    print("3. Implement a breadth-first search that fetches folder contents as needed")


async def main():
    """Run the debug script."""
    try:
        await debug_vault_structure()
    except KeyboardInterrupt:
        print("\nDebug interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("OBSIDIAN_REST_API_KEY"):
        print("ERROR: OBSIDIAN_REST_API_KEY environment variable must be set")
        sys.exit(1)
    
    asyncio.run(main())