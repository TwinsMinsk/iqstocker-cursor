#!/usr/bin/env python3
"""Script to run FastAPI admin panel."""

import uvicorn

if __name__ == "__main__":
    print("Starting IQStocker FastAPI Admin Panel...")
    print("Admin Panel: http://localhost:5000/admin")
    print("Health Check: http://localhost:5000/health")
    print("API Docs: http://localhost:5000/docs")
    
    uvicorn.run(
        "admin_fastapi:app",  # Import string instead of app object
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )
