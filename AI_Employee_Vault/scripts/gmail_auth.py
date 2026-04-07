"""
Gmail Authentication Script

One-time authentication to get Gmail API token.
Run this first before using gmail_watcher.py

Usage:
    python scripts/gmail_auth.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def authenticate_gmail():
    """Authenticate with Gmail API and save token."""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        import pickle
    except ImportError:
        print("Missing dependencies. Install with:")
        print("  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        sys.exit(1)
    
    # Paths
    vault_path = Path(__file__).parent.parent
    config_dir = vault_path / 'config' / 'gmail'
    config_dir.mkdir(parents=True, exist_ok=True)
    
    credentials_path = config_dir / 'credentials.json'
    token_path = config_dir / 'token.pickle'
    
    # Copy credentials if exists in root
    root_creds = Path(__file__).parent.parent.parent / 'credentails.json'
    if root_creds.exists() and not credentials_path.exists():
        import shutil
        shutil.copy2(root_creds, credentials_path)
        print(f"Copied credentials from {root_creds}")
    
    if not credentials_path.exists():
        print(f"Error: credentials.json not found at {credentials_path}")
        print("Please ensure credentails.json exists in the project root.")
        sys.exit(1)

    # Gmail API scopes - including modify to mark as read
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify',  # Can mark as read/unread
        'https://www.googleapis.com/auth/gmail.send'
    ]

    creds = None
    
    # Load existing token
    if token_path.exists():
        with open(token_path, 'rb') as f:
            creds = pickle.load(f)
    
    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES
            )
            print("\nOpening browser for Gmail authentication...")
            print("Please sign in with your Google account and grant permissions.")
            creds = flow.run_local_server(port=0)
        
        # Save token for future use
        with open(token_path, 'wb') as f:
            pickle.dump(creds, f)
            print(f"\n✓ Token saved to: {token_path}")
    
    # Test connection
    try:
        from googleapiclient.discovery import build
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        print(f"\n✓ Authentication successful!")
        print(f"  Logged in as: {profile['emailAddress']}")
        print(f"  Account: {profile.get('displayName', 'N/A')}")
        return True
    except Exception as e:
        print(f"\n✗ Authentication test failed: {e}")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("Gmail Authentication for AI Employee")
    print("=" * 60)
    
    if authenticate_gmail():
        print("\n" + "=" * 60)
        print("SUCCESS! Gmail is now authenticated.")
        print("You can now run: python scripts/gmail_watcher.py")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("FAILED! Please check the error above and try again.")
        print("=" * 60)
        sys.exit(1)
