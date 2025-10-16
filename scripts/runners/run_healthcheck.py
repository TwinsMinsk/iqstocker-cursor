#!/usr/bin/env python3
"""
Simple healthcheck service for Railway
This service only runs healthcheck endpoint
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🏥 Starting healthcheck service for Railway...")
    
    # Import and run healthcheck
    from healthcheck import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    port = int(os.getenv('PORT', 5000))
    print(f"🌐 Starting healthcheck on port {port}")
    
    app.run(host='0.0.0.0', port=port, debug=False)
