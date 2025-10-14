#!/usr/bin/env python3
"""Script to run FastAPI admin panel."""

import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    print(f"Starting IQStocker FastAPI Admin Panel on port {port}...")
    print(f"Admin Panel: http://localhost:{port}/admin")
    print(f"Health Check: http://localhost:{port}/health")
    print(f"API Docs: http://localhost:{port}/docs")
    
    uvicorn.run(
        "admin_fastapi:app",  # Import string instead of app object
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        log_level="info"
    )
