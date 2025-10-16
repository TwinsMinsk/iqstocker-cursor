import os
import sys
"""Test all admin panel pages after fixes."""

import requests
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

def test_all_admin_pages():
    """Test all admin panel pages."""
    
    print("🌐 Testing all admin panel pages...")
    
    base_url = "http://localhost:5000"
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(2)
    
    try:
        # Login first
        session = requests.Session()
        login_data = {'username': 'admin', 'password': 'admin123'}
        
        print("   🔐 Logging in...")
        login_response = session.post(f"{base_url}/admin/login", data=login_data, timeout=5)
        
        if 'dashboard' not in login_response.url and not login_response.url.endswith('/admin'):
            print("   ❌ Login failed")
            return False
        
        print("   ✅ Login successful!")
        
        # Test all pages
        pages = [
            ("/admin", "Dashboard"),
            ("/admin/users", "Users"),
            ("/admin/broadcast", "Broadcast"),
            ("/admin/content", "Content"),
            ("/admin/api/stats", "Stats API"),
            ("/admin/api/health", "Health API")
        ]
        
        results = {}
        
        for page_url, page_name in pages:
            try:
                print(f"   Testing {page_name}...")
                response = session.get(f"{base_url}{page_url}", timeout=5)
                
                if response.status_code == 200:
                    print(f"   ✅ {page_name} - OK")
                    results[page_name] = "OK"
                else:
                    print(f"   ❌ {page_name} - Error {response.status_code}")
                    results[page_name] = f"Error {response.status_code}"
                    
            except Exception as e:
                print(f"   ❌ {page_name} - Exception: {e}")
                results[page_name] = f"Exception: {e}"
        
        # Summary
        print("\n📊 Test Results Summary:")
        for page_name, result in results.items():
            status = "✅" if result == "OK" else "❌"
            print(f"   {status} {page_name}: {result}")
        
        # Check if all pages work
        all_ok = all(result == "OK" for result in results.values())
        
        if all_ok:
            print("\n🎉 All pages are working correctly!")
            return True
        else:
            print("\n⚠️ Some pages have issues.")
            return False
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to admin panel. Make sure it's running.")
        return False
    except Exception as e:
        print(f"❌ Error testing pages: {e}")
        return False


def test_broadcast_functionality():
    """Test broadcast functionality."""
    
    print("\n📢 Testing broadcast functionality...")
    
    base_url = "http://localhost:5000"
    
    try:
        # Login
        session = requests.Session()
        login_data = {'username': 'admin', 'password': 'admin123'}
        session.post(f"{base_url}/admin/login", data=login_data, timeout=5)
        
        # Test broadcast form
        broadcast_data = {
            'message': 'Test broadcast message from automated test',
            'subscription_type': 'all'
        }
        
        print("   Sending test broadcast...")
        response = session.post(f"{base_url}/admin/broadcast", data=broadcast_data, timeout=5)
        
        if response.status_code == 200:
            print("   ✅ Broadcast form submitted successfully")
            return True
        else:
            print(f"   ❌ Broadcast form error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Broadcast test error: {e}")
        return False


def main():
    """Run all admin panel tests."""
    
    print("🚀 Starting comprehensive admin panel tests...\n")
    
    # Test all pages
    pages_ok = test_all_admin_pages()
    
    # Test broadcast functionality
    broadcast_ok = test_broadcast_functionality()
    
    # Final summary
    print("\n" + "="*50)
    print("📋 FINAL TEST SUMMARY")
    print("="*50)
    
    if pages_ok and broadcast_ok:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Admin panel is fully functional")
        print("✅ All pages load correctly")
        print("✅ Broadcast functionality works")
        print("\n🚀 Admin panel is ready for use!")
    else:
        print("⚠️ SOME TESTS FAILED")
        if not pages_ok:
            print("❌ Some pages have issues")
        if not broadcast_ok:
            print("❌ Broadcast functionality has issues")
        print("\n🔧 Please check the errors above")


if __name__ == "__main__":
    main()
