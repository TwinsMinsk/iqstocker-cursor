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
            conn.execute("SELECT 1")
        
        return jsonify({
            "status": "healthy",
            "service": "iqstocker-bot",
            "database": "connected",
            "settings": "loaded"
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "service": "iqstocker-bot",
            "error": str(e)
        }), 500

@app.route('/')
def root():
    """Root endpoint."""
    return jsonify({
        "service": "IQStocker Bot",
        "status": "running",
        "version": "1.0.0"
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
