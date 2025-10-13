#!/usr/bin/env python3
"""Debug script to check admin settings."""

import os
from config.settings import settings

def debug_admin_settings():
    """Debug admin settings."""
    print("🔍 Debugging Admin Settings")
    print("=" * 50)
    
    # Check environment variables
    print("Environment Variables:")
    admin_vars = {
        'ADMIN_USERNAME': os.getenv('ADMIN_USERNAME'),
        'ADMIN_PASSWORD': os.getenv('ADMIN_PASSWORD'),
        'ADMIN_SECRET_KEY': os.getenv('ADMIN_SECRET_KEY')
    }
    
    for var, value in admin_vars.items():
        if value:
            print(f"  {var}: {value}")
        else:
            print(f"  {var}: Not set")
    
    print("\nSettings Values:")
    print(f"  Username: '{settings.admin.username}'")
    print(f"  Password: '{settings.admin.password}'")
    print(f"  Secret Key: '{settings.admin.secret_key[:20]}...'")
    
    print("\nBackward Compatibility:")
    print(f"  admin_username: '{settings.admin_username}'")
    print(f"  admin_password: '{settings.admin_password}'")
    print(f"  admin_secret_key: '{settings.admin_secret_key[:20]}...'")
    
    # Test authentication logic
    print("\nAuthentication Test:")
    test_username = "admin"
    test_password = "admin123"
    
    username_match = test_username == settings.admin.username
    password_match = test_password == settings.admin.password
    
    print(f"  Test username '{test_username}' matches: {username_match}")
    print(f"  Test password '{test_password}' matches: {password_match}")
    
    if username_match and password_match:
        print("  ✅ Authentication should work!")
    else:
        print("  ❌ Authentication will fail!")
        print(f"  Expected username: '{settings.admin.username}'")
        print(f"  Expected password: '{settings.admin.password}'")
    
    return username_match and password_match

if __name__ == "__main__":
    debug_admin_settings()
