import uvicorn
import sys

if __name__ == "__main__":
    sys.stdout = open("backend.log", "w")
    sys.stderr = open("backend.log", "a")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
