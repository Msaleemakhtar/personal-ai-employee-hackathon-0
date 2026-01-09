"""
OAuth2 authentication for Gmail MCP server.

Handles credential discovery, loading, refresh, and interactive OAuth flow.
"""

import os
import json
from pathlib import Path
from typing import Optional
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',  # Read, compose, send, and modify
    'https://www.googleapis.com/auth/gmail.labels',   # Manage labels
]

# Standard credential locations
DEFAULT_CREDS_DIR = Path.home() / '.gmail-mcp'
DEFAULT_TOKEN_FILE = DEFAULT_CREDS_DIR / 'credentials.json'
DEFAULT_OAUTH_CONFIG = DEFAULT_CREDS_DIR / 'oauth-credentials.json'

# Alternative location (project-specific)
PROJECT_OAUTH_CONFIG = Path('/home/salim/Desktop/hackathon0/gcp-oauth.keys.json')


def find_oauth_config() -> Optional[Path]:
    """
    Find OAuth client configuration file.

    Search order:
    1. ~/.gmail-mcp/oauth-credentials.json
    2. /home/salim/Desktop/hackathon0/gcp-oauth.keys.json
    3. Environment variable GMAIL_OAUTH_CONFIG

    Returns:
        Path to OAuth config file, or None if not found
    """
    # Check environment variable first
    env_path = os.getenv('GMAIL_OAUTH_CONFIG')
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path

    # Check standard location
    if DEFAULT_OAUTH_CONFIG.exists():
        return DEFAULT_OAUTH_CONFIG

    # Check project location
    if PROJECT_OAUTH_CONFIG.exists():
        return PROJECT_OAUTH_CONFIG

    return None


def run_oauth_flow(oauth_config_path: Path, token_path: Path) -> Credentials:
    """
    Run interactive OAuth2 authorization flow.

    Opens browser for user to authorize application. Saves resulting
    credentials to token_path.

    Args:
        oauth_config_path: Path to OAuth client configuration JSON
        token_path: Path to save resulting credentials

    Returns:
        Credentials object

    Raises:
        FileNotFoundError: If oauth_config_path doesn't exist
        ValueError: If OAuth flow fails
    """
    if not oauth_config_path.exists():
        raise FileNotFoundError(f"OAuth config not found: {oauth_config_path}")

    # Ensure token directory exists
    token_path.parent.mkdir(parents=True, exist_ok=True)

    # Run OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(
        str(oauth_config_path),
        SCOPES
    )

    # This will open a browser window
    creds = flow.run_local_server(port=0)

    # Save credentials
    with open(token_path, 'w') as f:
        f.write(creds.to_json())

    return creds


def load_credentials(token_path: Optional[Path] = None) -> Optional[Credentials]:
    """
    Load existing credentials from file.

    Args:
        token_path: Path to credentials file (default: ~/.gmail-mcp/credentials.json)

    Returns:
        Credentials object if found and valid, None otherwise
    """
    if token_path is None:
        token_path = DEFAULT_TOKEN_FILE

    if not token_path.exists():
        return None

    try:
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        return creds
    except Exception:
        return None


def refresh_credentials(creds: Credentials, token_path: Optional[Path] = None) -> Credentials:
    """
    Refresh expired credentials.

    Args:
        creds: Credentials object to refresh
        token_path: Path to save refreshed credentials

    Returns:
        Refreshed credentials

    Raises:
        Exception: If refresh fails
    """
    if token_path is None:
        token_path = DEFAULT_TOKEN_FILE

    creds.refresh(Request())

    # Save refreshed credentials
    token_path.parent.mkdir(parents=True, exist_ok=True)
    with open(token_path, 'w') as f:
        f.write(creds.to_json())

    return creds


def get_credentials(
    token_path: Optional[Path] = None,
    oauth_config_path: Optional[Path] = None,
    interactive: bool = True
) -> Credentials:
    """
    Get valid Gmail API credentials.

    This is the main entry point for authentication. It handles:
    1. Loading existing credentials
    2. Refreshing expired credentials
    3. Running interactive OAuth flow if needed

    Args:
        token_path: Path to credentials file (default: ~/.gmail-mcp/credentials.json)
        oauth_config_path: Path to OAuth client config (auto-discovered if None)
        interactive: Allow interactive OAuth flow if credentials not found

    Returns:
        Valid Credentials object

    Raises:
        FileNotFoundError: If OAuth config not found and interactive=True
        ValueError: If credentials invalid and interactive=False
    """
    if token_path is None:
        token_path = DEFAULT_TOKEN_FILE

    # Try to load existing credentials
    creds = load_credentials(token_path)

    # Check if credentials are valid
    if creds and creds.valid:
        return creds

    # Try to refresh expired credentials
    if creds and creds.expired and creds.refresh_token:
        try:
            return refresh_credentials(creds, token_path)
        except Exception:
            # Refresh failed, need to re-authenticate
            pass

    # Need new credentials via OAuth flow
    if not interactive:
        raise ValueError(
            "No valid credentials found. Run with --auth flag or set up credentials manually."
        )

    # Find OAuth config
    if oauth_config_path is None:
        oauth_config_path = find_oauth_config()

    if oauth_config_path is None:
        raise FileNotFoundError(
            f"OAuth client configuration not found. Please create one at:\n"
            f"  {DEFAULT_OAUTH_CONFIG}\n"
            f"or set GMAIL_OAUTH_CONFIG environment variable.\n\n"
            f"To create OAuth credentials:\n"
            f"1. Go to https://console.cloud.google.com/apis/credentials\n"
            f"2. Create OAuth 2.0 Client ID (Desktop application)\n"
            f"3. Download JSON file\n"
            f"4. Save it to {DEFAULT_OAUTH_CONFIG}"
        )

    # Run interactive OAuth flow
    return run_oauth_flow(oauth_config_path, token_path)


def setup_auth_interactive():
    """
    Interactive authentication setup.

    Guides user through OAuth flow and saves credentials.
    Intended for CLI --auth command.
    """
    print("Gmail MCP Server - Authentication Setup")
    print("=" * 50)
    print()

    # Find OAuth config
    oauth_config = find_oauth_config()

    if oauth_config is None:
        print("ERROR: OAuth client configuration not found.")
        print()
        print("Please follow these steps:")
        print("1. Go to https://console.cloud.google.com/apis/credentials")
        print("2. Create a new project (if needed)")
        print("3. Enable Gmail API")
        print("4. Create OAuth 2.0 Client ID (Desktop application)")
        print("5. Download the JSON file")
        print(f"6. Save it to: {DEFAULT_OAUTH_CONFIG}")
        print()
        print("Then run this command again.")
        return False

    print(f"Found OAuth config: {oauth_config}")
    print()
    print("Opening browser for authorization...")
    print("Please authorize the application in your browser.")
    print()

    try:
        creds = run_oauth_flow(oauth_config, DEFAULT_TOKEN_FILE)
        print()
        print("✓ Authentication successful!")
        print(f"✓ Credentials saved to: {DEFAULT_TOKEN_FILE}")
        print()
        print("You can now use the Gmail MCP server.")
        return True

    except Exception as e:
        print()
        print(f"ERROR: Authentication failed: {e}")
        return False
