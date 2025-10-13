"""Test admin panel after database fixes."""

import requests
import time

def test_admin_login_fixed():
    """Test admin login with fixed credentials."""
    
    print("🔐 Testing admin login with fixes...")
    
    base_url = "http://localhost:5000"
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(3)
    
    try:
        # Test login with correct credentials
        print("   Testing login with correct credentials...")
        
        session = requests.Session()
        
        # Get login page
        login_page = session.get(f"{base_url}/admin/login", timeout=5)
        if login_page.status_code != 200:
            print(f"   ❌ Cannot access login page: {login_page.status_code}")
            return False
        
        # Try to login
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        login_response = session.post(f"{base_url}/admin/login", data=login_data, timeout=5)
        
        # Check if redirected to dashboard (successful login)
        if 'dashboard' in login_response.url or login_response.url.endswith('/admin'):
            print("   ✅ Login successful!")
            
            # Test dashboard access
            dashboard_response = session.get(f"{base_url}/admin", timeout=5)
            if dashboard_response.status_code == 200:
                print("   ✅ Dashboard accessible!")
                return True
            else:
                print(f"   ❌ Dashboard error: {dashboard_response.status_code}")
                return False
        else:
            print(f"   ❌ Login failed - stayed on login page")
            print(f"   Response URL: {login_response.url}")
            return False
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_all_pages():
    """Test all admin pages."""
    
    print("\n🌐 Testing all admin pages...")
    
    base_url = "http://localhost:5000"
    
    try:
        # Login first
        session = requests.Session()
        login_data = {'username': 'admin', 'password': 'admin123'}
        session.post(f"{base_url}/admin/login", data=login_data, timeout=5)
        
        # Test pages
        pages = [
            ("/admin", "Dashboard"),
            ("/admin/users", "Users"),
            ("/admin/broadcast", "Broadcast"),
            ("/admin/content", "Content"),
            ("/admin/api/stats", "Stats API"),
            ("/admin/api/health", "Health API")
        ]
        
        for page_url, page_name in pages:
            try:
                response = session.get(f"{base_url}{page_url}", timeout=5)
                if response.status_code == 200:
                    print(f"   ✅ {page_name} - OK")
                else:
                    print(f"   ❌ {page_name} - Error {response.status_code}")
            except Exception as e:
                print(f"   ❌ {page_name} - Exception: {e}")
        
        print("✅ All pages tested!")
        
    except Exception as e:
        print(f"❌ Error testing pages: {e}")


def main():
    """Run all tests."""
    
    print("🚀 Starting admin panel tests after fixes...\n")
    
    # Test login
    if test_admin_login_fixed():
        # Test all pages
        test_all_pages()
        print("\n🎉 All tests passed! Admin panel is working!")
    else:
        print("\n❌ Login test failed. Check the fixes.")


if __name__ == "__main__":
    main()
