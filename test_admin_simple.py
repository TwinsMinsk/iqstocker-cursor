"""Simple test for admin panel pages."""

import requests
import time

def test_admin_pages():
    """Test admin panel pages."""
    
    print("🌐 Testing admin panel pages...")
    
    base_url = "http://localhost:5000"
    
    try:
        # Create session
        session = requests.Session()
        
        # Login
        print("   🔐 Logging in...")
        login_data = {'username': 'admin', 'password': 'admin123'}
        login_response = session.post(f"{base_url}/admin/login", data=login_data, timeout=10)
        
        if login_response.status_code != 200:
            print(f"   ❌ Login failed: {login_response.status_code}")
            return False
        
        print("   ✅ Login successful!")
        
        # Test dashboard
        print("   Testing dashboard...")
        dashboard_response = session.get(f"{base_url}/admin", timeout=10)
        if dashboard_response.status_code == 200:
            print("   ✅ Dashboard - OK")
        else:
            print(f"   ❌ Dashboard - Error {dashboard_response.status_code}")
        
        # Test users page
        print("   Testing users page...")
        users_response = session.get(f"{base_url}/admin/users", timeout=10)
        if users_response.status_code == 200:
            print("   ✅ Users - OK")
        else:
            print(f"   ❌ Users - Error {users_response.status_code}")
        
        # Test broadcast page
        print("   Testing broadcast page...")
        broadcast_response = session.get(f"{base_url}/admin/broadcast", timeout=10)
        if broadcast_response.status_code == 200:
            print("   ✅ Broadcast - OK")
        else:
            print(f"   ❌ Broadcast - Error {broadcast_response.status_code}")
        
        # Test content page
        print("   Testing content page...")
        content_response = session.get(f"{base_url}/admin/content", timeout=10)
        if content_response.status_code == 200:
            print("   ✅ Content - OK")
        else:
            print(f"   ❌ Content - Error {content_response.status_code}")
        
        print("\n🎉 All pages tested!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    test_admin_pages()
