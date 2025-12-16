import uvicorn
import sys

if __name__ == "__main__":
    print("🔥 Starting FastAPI backend on port 8000")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
