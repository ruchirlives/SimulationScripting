#!/usr/bin/env python3
"""
OAuth Debug Script
Run this to check your Google OAuth configuration
"""

import os

def check_oauth_config():
    """Check if OAuth environment variables are set."""
    
    print("=== Google OAuth Configuration Check ===")
    print()
    
    # Check required environment variables
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    flask_secret = os.environ.get("FLASK_SECRET_KEY")
    
    print(f"GOOGLE_CLIENT_ID: {'✓ Set' if client_id else '✗ Missing'}")
    if client_id:
        print(f"  Value: {client_id[:20]}...")
    
    print(f"GOOGLE_CLIENT_SECRET: {'✓ Set' if client_secret else '✗ Missing'}")
    if client_secret:
        print(f"  Value: {client_secret[:10]}...")
    
    print(f"FLASK_SECRET_KEY: {'✓ Set' if flask_secret else '✗ Using fallback'}")
    
    print()
    print("=== Instructions ===")
    
    if not client_id or not client_secret:
        print("Missing OAuth credentials! You need to:")
        print("1. Go to https://console.developers.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable the Google+ API")
        print("4. Create OAuth 2.0 credentials")
        print("5. Add http://localhost:5000/login/google/authorized as redirect URI")
        print("6. Set environment variables:")
        print("   export GOOGLE_CLIENT_ID='your_client_id'")
        print("   export GOOGLE_CLIENT_SECRET='your_client_secret'")
        print("   export FLASK_SECRET_KEY='your_secret_key'")
    else:
        print("OAuth credentials are configured!")
        print("Make sure your redirect URI in Google Console is:")
        print("http://localhost:5000/login/google/authorized")
    
    print()
    print("=== Test URLs ===")
    print("After starting your Flask app, try:")
    print("- Main app: http://localhost:5000/")
    print("- Auth debug: http://localhost:5000/debug-auth")
    print("- Manual login: http://localhost:5000/login/google")

if __name__ == "__main__":
    check_oauth_config()
