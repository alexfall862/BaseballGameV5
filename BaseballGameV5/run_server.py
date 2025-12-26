"""
Server entry point for Railway deployment.

Run with: python run_server.py
or: uvicorn run_server:app --host 0.0.0.0 --port 8000
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from api.app import app

# Re-export app for uvicorn
__all__ = ["app"]


if __name__ == "__main__":
    # Get port from environment (Railway sets this)
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")

    print(f"Starting Baseball Simulation API on {host}:{port}")

    uvicorn.run(
        "run_server:app",
        host=host,
        port=port,
        reload=False,
        workers=1,  # Single worker for deterministic results
    )
