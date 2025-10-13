"""Test admin login functionality."""

import requests
import time

def test_admin_login():
    """Test admin login with different credentials."""
    
    print("🔐 Testing admin login...")
    
    base_url = "http://localhost:5000"
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(3)
    
    try:
        # Test cases
        test_cases = [
            ("admin", "admin123", "Correct credentials"),
            ("admin", "wrong", "Wrong password"),
            ("wrong", "admin123", "Wrong username"),
            ("", "", "Empty credentials"),
            ("admin ", "admin123", "Username with space"),
            (" admin", "admin123", "Username with leading space"),
        ]
        
        for username, password, description in test_cases:
            print(f"\n   Testing: {description}")
            print(f"   Username: '{username}', Password: '{password}'")
            
            try:
                # Get login page first
                session = requests.Session()
                login_page = session.get(f"{base_url}/admin/login", timeout=5)
                
                if login_page.status_code != 200:
                    print(f"   ❌ Cannot access login page: {login_page.status_code}")
                    continue
                
                # Try to login
                login_data = {
                    'username': username,
                    'password': password
                }
                
                login_response = session.post(f"{base_url}/admin/login", data=login_data, timeout=5)
                
                # Check if redirected to dashboard (successful login)
                if 'dashboard' in login_response.url or login_response.url.endswith('/admin'):
                    print(f"   ✅ Login successful - redirected to dashboard")
                else:
                    print(f"   ❌ Login failed - stayed on login page")
                    print(f"   Response URL: {login_response.url}")
                
            except requests.exceptions.RequestException as e:
                print(f"   ❌ Request error: {e}")
        
        print("\n✅ Login tests completed!")
        
    except Exception as e:
        print(f"❌ Error testing login: {e}")


def check_server_status():
    """Check if server is running."""
    
    print("🌐 Checking server status...")
    
    try:
        response = requests.get("http://localhost:5000/admin/login", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and accessible")
            return True
        else:
            print(f"❌ Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running or not accessible")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False


def main():
    """Run login tests."""
    
    print("🚀 Starting admin login tests...\n")
    
    # Check server status
    if check_server_status():
        # Run login tests
        test_admin_login()
    else:
        print("❌ Cannot run tests - server is not accessible")
        print("Make sure to run: python admin_panel.py")


if __name__ == "__main__":
    main()
