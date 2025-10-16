import os
import sys
#!/usr/bin/env python3
"""Test authentication with new credentials."""

from config.settings import settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_new_credentials():
    """Test authentication with new credentials."""
    print("Testing authentication with new credentials...")
    print("=" * 50)
    
    # Test credentials from .env
    test_username = "IQStocker"
    test_password = "Punkrock77"
    
    print(f"Testing username: '{test_username}'")
    print(f"Testing password: '{test_password}'")
    print()
    
    print("Current settings:")
    print(f"  Username: '{settings.admin.username}'")
    print(f"  Password: '{settings.admin.password}'")
    print()
    
    # Test authentication
    username_match = test_username == settings.admin.username
    password_match = test_password == settings.admin.password
    
    print("Authentication test:")
    print(f"  Username match: {username_match}")
    print(f"  Password match: {password_match}")
    print()
    
    if username_match and password_match:
        print("✅ SUCCESS! Authentication should work!")
        print("You can now login with:")
        print(f"  Username: {test_username}")
        print(f"  Password: {test_password}")
    else:
        print("❌ FAILED! Authentication will not work!")
        print("Expected:")
        print(f"  Username: '{settings.admin.username}'")
        print(f"  Password: '{settings.admin.password}'")
    
    return username_match and password_match

if __name__ == "__main__":
    test_new_credentials()
