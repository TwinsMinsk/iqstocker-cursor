#!/usr/bin/env python3
"""Script to run FastAPI admin panel."""

import os
import uvicorn
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    print(f"Starting IQStocker FastAPI Admin Panel on port {port}...")
    print(f"Admin Panel: http://localhost:{port}/admin")
    print(f"Dashboard: http://localhost:{port}/dashboard")
    print(f"API Docs: http://localhost:{port}/docs")
    
    uvicorn.run(
        "admin_panel.main:app",  # Import string for new admin panel
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        log_level="info"
    )
