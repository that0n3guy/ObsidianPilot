#!/usr/bin/env python3
"""Configure Claude Desktop to use Obsidian MCP server."""

import json
import os
import sys
import platform
import argparse
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class ConfigManager:
    """Manages Claude Desktop configuration for Obsidian MCP."""
    
    def __init__(self):
        self.config_path = self._get_config_path()
        self.config: Dict[str, Any] = {}
        
    def _get_config_path(self) -> Path:
        """Get Claude Desktop config path based on OS."""
        system = platform.system()
        
        if system == "Darwin":  # macOS
            config_dir = Path.home() / "Library" / "Application Support" / "Claude"
        elif system == "Windows":
            config_dir = Path(os.environ["APPDATA"]) / "Claude"
        elif system == "Linux":
            config_dir = Path.home() / ".config" / "Claude"
        else:
            raise ValueError(f"Unsupported operating system: {system}")
            
        config_path = config_dir / "claude_desktop_config.json"
        return config_path
    
    def load_config(self) -> bool:
        """Load existing config or create empty one."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                return True
            except json.JSONDecodeError:
                print(f"⚠️  Warning: Invalid JSON in {self.config_path}")
                self.config = {}
                return False
        else:
            print(f"📝 Creating new config at {self.config_path}")
            self.config = {"mcpServers": {}}
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            return False
    
    def backup_config(self) -> Optional[Path]:
        """Create backup of existing config."""
        if self.config_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.config_path.with_name(
                f"{self.config_path.stem}.backup_{timestamp}.json"
            )
            shutil.copy2(self.config_path, backup_path)
            print(f"💾 Backup saved to: {backup_path.name}")
            return backup_path
        return None
    
    def detect_old_config(self, server_name: str = "obsidian") -> Optional[Dict[str, Any]]:
        """Detect if old REST API configuration exists."""
        if "mcpServers" not in self.config:
            return None
            
        servers = self.config["mcpServers"]
        if server_name not in servers:
            return None
            
        old_config = servers[server_name]
        
        # Check for indicators of old REST API config
        is_old = any([
            "cwd" in old_config,
            old_config.get("args") == ["-m", "src.server"],
            "OBSIDIAN_REST_API_KEY" in old_config.get("env", {}),
            "PYTHONPATH" in old_config.get("env", {}),
            old_config.get("command", "").endswith("python") or old_config.get("command", "").endswith("python3")
        ])
        
        return old_config if is_old else None
    
    def update_config(self, vault_path: str, server_name: str = "obsidian", force: bool = False) -> bool:
        """Update config with new Obsidian MCP settings."""
        # Ensure mcpServers exists
        if "mcpServers" not in self.config:
            self.config["mcpServers"] = {}
        
        # Check for existing config
        old_config = self.detect_old_config(server_name)
        
        if old_config:
            print("\n🔄 Migration detected!")
            print("Found old REST API configuration:")
            print(f"  - Command: {old_config.get('command', 'N/A')}")
            print(f"  - Working directory: {old_config.get('cwd', 'N/A')}")
            print("  - Using REST API plugin")
            print("\nMigrating to v2.0 direct filesystem access...")
            
            # Try to extract vault path from old config if not provided
            if not vault_path and "OBSIDIAN_VAULT_PATH" in old_config.get("env", {}):
                vault_path = old_config["env"]["OBSIDIAN_VAULT_PATH"]
                print(f"  - Reusing vault path: {vault_path}")
        elif server_name in self.config["mcpServers"] and not force:
            print(f"\n⚠️  Server '{server_name}' already exists in config.")
            response = input("Overwrite? (y/N): ").strip().lower()
            if response != 'y':
                print("❌ Configuration cancelled.")
                return False
        
        # Validate vault path
        vault_path = Path(vault_path).expanduser().resolve()
        if not vault_path.exists():
            print(f"❌ Vault path does not exist: {vault_path}")
            return False
        if not vault_path.is_dir():
            print(f"❌ Vault path is not a directory: {vault_path}")
            return False
            
        # Create new config
        new_config = {
            "command": "uvx",
            "args": ["obsidian-mcp"],
            "env": {
                "OBSIDIAN_VAULT_PATH": str(vault_path)
            }
        }
        
        # Update config
        self.config["mcpServers"][server_name] = new_config
        
        # Show what changed
        if old_config:
            print("\n✅ Migration complete!")
            print("  - Removed dependency on Local REST API plugin")
            print("  - Now using direct filesystem access (faster!)")
            print(f"  - Vault path: {vault_path}")
        else:
            print(f"\n✅ Added Obsidian MCP server '{server_name}'")
            print(f"  - Vault path: {vault_path}")
            
        return True
    
    def save_config(self) -> None:
        """Save config to file with pretty formatting."""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        print(f"\n💾 Configuration saved to: {self.config_path}")
        
    def show_usage(self) -> None:
        """Show how to use the configured server."""
        print("\n🚀 Setup complete! Restart Claude Desktop to use Obsidian MCP.")
        print("\nExample prompts to try:")
        print("  - 'Show me all notes I modified this week'")
        print("  - 'Create a new daily note for today'")
        print("  - 'Search for all notes about project planning'")


def main():
    """Main entry point for configuration script."""
    parser = argparse.ArgumentParser(
        description="Configure Claude Desktop to use Obsidian MCP server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Configure with your vault
  obsidian-mcp-configure --vault-path /path/to/vault
  
  # Use custom server name
  obsidian-mcp-configure --vault-path /path/to/vault --name my-vault
  
  # Force overwrite without prompting
  obsidian-mcp-configure --vault-path /path/to/vault --force
"""
    )
    
    parser.add_argument(
        "--vault-path",
        type=str,
        required=True,
        help="Path to your Obsidian vault"
    )
    
    parser.add_argument(
        "--name",
        type=str,
        default="obsidian",
        help="Server name in Claude config (default: obsidian)"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite existing config without prompting"
    )
    
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup of existing config"
    )
    
    args = parser.parse_args()
    
    # Header
    print("🔮 Obsidian MCP Configuration Tool")
    print("=" * 40)
    
    try:
        # Initialize config manager
        manager = ConfigManager()
        
        # Load existing config
        config_exists = manager.load_config()
        
        # Create backup if requested and config exists
        if config_exists and not args.no_backup:
            manager.backup_config()
        
        # Update configuration
        success = manager.update_config(
            vault_path=args.vault_path,
            server_name=args.name,
            force=args.force
        )
        
        if success:
            # Save config
            manager.save_config()
            
            # Show usage instructions
            manager.show_usage()
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()