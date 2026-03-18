"""
fastapi_backend/__main__.py

Entry point for: python -m fastapi_backend.app
Starts the Uvicorn server on host 0.0.0.0, port 5001.
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "fastapi_backend.app:app",
        host="0.0.0.0",
        port=5001,
        reload=True,
    )
