import sys
"""Health check endpoint for Railway deployment."""

from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/health')
def health_check():
    """Health check endpoint for Railway."""
    try:
        # Check if we can import main modules
        from config.settings import settings
        from config.database import engine
        
        # Test database connection
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        
        return jsonify({
            "status": "healthy",
            "service": "iqstocker-bot",
            "database": "connected",
            "settings": "loaded",
            "admin_panel": "available"
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "service": "iqstocker-bot",
            "error": str(e)
        }), 500

def check_health():
    """Health check function for testing."""
    try:
        # Check if we can import main modules
        from config.settings import settings
        from config.database import engine
        
        # Test database connection
        with engine.connect() as conn:
            from sqlalchemy import text
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            conn.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "service": "iqstocker-bot",
            "database": "connected",
            "settings": "loaded",
            "admin_panel": "available",
            "timestamp": "2023-10-27T10:00:00Z"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2023-10-27T10:00:00Z"
        }

@app.route('/')
def root():
    """Root endpoint."""
    return jsonify({
        "service": "IQStocker Bot",
        "status": "running",
        "version": "1.0.0",
        "admin_panel": "http://localhost:5000/admin"
    }), 200

@app.route('/admin')
def admin_redirect():
    """Redirect to admin panel."""
    return jsonify({
        "message": "Admin panel is available",
        "url": "http://localhost:5000/admin",
        "note": "Use FastAPI admin panel for full functionality"
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
