"""
Gmail MCP Server - Entry point and CLI.

Provides command-line interface for running the server and managing authentication.
"""

import sys
import argparse
from pathlib import Path
from gmail_mcp.auth import setup_auth_interactive, find_oauth_config, DEFAULT_TOKEN_FILE
from gmail_mcp.server import mcp


def main():
    """Main entry point for Gmail MCP server."""
    parser = argparse.ArgumentParser(
        prog="gmail-mcp",
        description="Gmail MCP Server - Connect Gmail to Claude and other MCP clients",
        epilog="For more information, see: https://github.com/your-repo/gmail-mcp-server"
    )

    parser.add_argument(
        "--auth",
        action="store_true",
        help="Run interactive OAuth authentication flow"
    )

    parser.add_argument(
        "--check-auth",
        action="store_true",
        help="Check if valid credentials exist"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )

    args = parser.parse_args()

    # Handle authentication setup
    if args.auth:
        success = setup_auth_interactive()
        sys.exit(0 if success else 1)

    # Handle authentication check
    if args.check_auth:
        if DEFAULT_TOKEN_FILE.exists():
            print(f"✓ Credentials found: {DEFAULT_TOKEN_FILE}")

            # Try to load and validate
            try:
                from gmail_mcp.auth import load_credentials
                creds = load_credentials()
                if creds and creds.valid:
                    print("✓ Credentials are valid")
                    sys.exit(0)
                elif creds and creds.expired:
                    print("⚠ Credentials expired (will auto-refresh)")
                    sys.exit(0)
                else:
                    print("✗ Credentials invalid")
                    sys.exit(1)
            except Exception as e:
                print(f"✗ Error loading credentials: {e}")
                sys.exit(1)
        else:
            print(f"✗ No credentials found at: {DEFAULT_TOKEN_FILE}")
            print()
            print("Run: gmail-mcp --auth")
            sys.exit(1)

    # Default: Run the MCP server
    try:
        # Check for credentials before starting
        if not DEFAULT_TOKEN_FILE.exists():
            oauth_config = find_oauth_config()
            if oauth_config:
                print("No credentials found. Running authentication flow...", file=sys.stderr)
                print(file=sys.stderr)
                success = setup_auth_interactive()
                if not success:
                    print("Authentication failed. Exiting.", file=sys.stderr)
                    sys.exit(1)
            else:
                print("ERROR: No credentials found.", file=sys.stderr)
                print(file=sys.stderr)
                print("Run: gmail-mcp --auth", file=sys.stderr)
                sys.exit(1)

        # Start the MCP server with stdio transport
        print("Starting Gmail MCP server...", file=sys.stderr)
        mcp.run()

    except KeyboardInterrupt:
        print("\nShutting down Gmail MCP server...", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
