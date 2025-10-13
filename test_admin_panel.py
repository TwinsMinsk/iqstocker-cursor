#!/usr/bin/env python3
"""Test script to verify admin panel functionality."""

import requests
import time
import subprocess
import sys
import os

def test_admin_panel():
    """Test admin panel functionality."""
    print("🧪 Testing IQStocker FastAPI Admin Panel...")
    print("=" * 50)
    
    # Test 1: Check if server is running
    print("1. Testing server startup...")
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            print(f"   Database: {data.get('database', 'unknown')}")
            print(f"   Admin panel: {data.get('admin_panel', 'unknown')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Please start it first.")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Check root endpoint
    print("\n2. Testing root endpoint...")
    try:
        response = requests.get("http://localhost:5000/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root endpoint works: {data['service']}")
            print(f"   Admin URL: {data.get('admin_url', 'unknown')}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
    
    # Test 3: Check admin panel access
    print("\n3. Testing admin panel access...")
    try:
        response = requests.get("http://localhost:5000/admin", timeout=5)
        if response.status_code == 200:
            print("✅ Admin panel is accessible")
            print("   Login page should be displayed")
        elif response.status_code == 401:
            print("✅ Admin panel requires authentication (expected)")
        else:
            print(f"❌ Admin panel access failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Admin panel access error: {e}")
    
    # Test 4: Check API documentation
    print("\n4. Testing API documentation...")
    try:
        response = requests.get("http://localhost:5000/docs", timeout=5)
        if response.status_code == 200:
            print("✅ API documentation is accessible")
            print("   Swagger UI should be displayed")
        else:
            print(f"❌ API documentation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ API documentation error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Admin panel testing completed!")
    print("\n📋 Next steps:")
    print("1. Open http://localhost:5000/admin in your browser")
    print("2. Login with: admin / admin123")
    print("3. Explore the admin interface")
    print("4. Check API docs at http://localhost:5000/docs")
    
    return True

def start_server():
    """Start the admin panel server."""
    print("🚀 Starting admin panel server...")
    try:
        # Start server in background
        process = subprocess.Popen([
            sys.executable, "run_admin_fastapi.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a bit for server to start
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Server started successfully")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Server failed to start:")
            print(f"STDOUT: {stdout.decode()}")
            print(f"STDERR: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return None

def main():
    """Main test function."""
    print("🎛️ IQStocker Admin Panel Test Suite")
    print("=" * 50)
    
    # Check if server is already running
    try:
        response = requests.get("http://localhost:5000/health", timeout=2)
        print("✅ Server is already running")
        server_process = None
    except:
        print("⚠️  Server is not running, starting it...")
        server_process = start_server()
        if not server_process:
            print("❌ Failed to start server")
            return False
    
    # Run tests
    success = test_admin_panel()
    
    # Cleanup
    if server_process:
        print("\n🛑 Stopping test server...")
        server_process.terminate()
        server_process.wait()
        print("✅ Server stopped")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
