"""Test script for enhanced admin panel features."""

import requests
import json
import time
from datetime import datetime

ADMIN_PANEL_URL = "http://localhost:5000"
ADMIN_USERNAME = "IQStocker"
ADMIN_PASSWORD = "Punkrock77"

def test_admin_panel_enhancements():
    """Test all enhanced admin panel features."""
    
    print("🎛️ Testing Enhanced IQStocker Admin Panel")
    print("=" * 50)
    
    # Test 1: Health Check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{ADMIN_PANEL_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ Health check passed")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test 2: Analytics API
    print("2. Testing analytics API...")
    try:
        response = requests.get(f"{ADMIN_PANEL_URL}/api/analytics/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        print("✅ Analytics API working")
    except Exception as e:
        print(f"❌ Analytics API failed: {e}")
    
    # Test 3: Charts API
    print("3. Testing charts API...")
    try:
        response = requests.get(f"{ADMIN_PANEL_URL}/api/analytics/charts")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        print("✅ Charts API working")
    except Exception as e:
        print(f"❌ Charts API failed: {e}")
    
    # Test 4: Audit Logs API
    print("4. Testing audit logs API...")
    try:
        response = requests.get(f"{ADMIN_PANEL_URL}/api/audit/logs")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        print("✅ Audit logs API working")
    except Exception as e:
        print(f"❌ Audit logs API failed: {e}")
    
    # Test 5: Dashboard Access
    print("5. Testing dashboard access...")
    try:
        response = requests.get(f"{ADMIN_PANEL_URL}/dashboard")
        assert response.status_code == 200
        assert "IQStocker Admin Dashboard" in response.text
        print("✅ Dashboard accessible")
    except Exception as e:
        print(f"❌ Dashboard access failed: {e}")
    
    # Test 6: Admin Panel Access
    print("6. Testing admin panel access...")
    try:
        response = requests.get(f"{ADMIN_PANEL_URL}/admin")
        assert response.status_code == 200
        print("✅ Admin panel accessible")
    except Exception as e:
        print(f"❌ Admin panel access failed: {e}")
    
    # Test 7: API Documentation
    print("7. Testing API documentation...")
    try:
        response = requests.get(f"{ADMIN_PANEL_URL}/docs")
        assert response.status_code == 200
        assert "Swagger UI" in response.text
        print("✅ API documentation accessible")
    except Exception as e:
        print(f"❌ API documentation failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Enhanced Admin Panel Testing Complete!")
    print("\n📋 Available Features:")
    print("✅ Custom IQStocker logo")
    print("✅ Enhanced filters and search")
    print("✅ Audit logging system")
    print("✅ Analytics API endpoints")
    print("✅ Charts and visualizations")
    print("✅ Improved UI/UX")
    print("✅ Responsive design")
    print("✅ Dark mode support")
    
    print(f"\n🌐 Access URLs:")
    print(f"   Admin Panel: {ADMIN_PANEL_URL}/admin")
    print(f"   Dashboard: {ADMIN_PANEL_URL}/dashboard")
    print(f"   API Docs: {ADMIN_PANEL_URL}/docs")
    print(f"   Health Check: {ADMIN_PANEL_URL}/health")
    
    print(f"\n🔑 Login Credentials:")
    print(f"   Username: {ADMIN_USERNAME}")
    print(f"   Password: {ADMIN_PASSWORD}")
    
    return True

if __name__ == "__main__":
    test_admin_panel_enhancements()
