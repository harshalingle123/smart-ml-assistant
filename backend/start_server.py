"""
Start the FastAPI server with proper configuration for large file uploads
"""
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        # Increase timeout for large file uploads
        timeout_keep_alive=300,  # 5 minutes
        # Limit concurrent connections to manage memory
        limit_concurrency=100,
        # Log level
        log_level="info",
        # Access log
        access_log=True,
    )
