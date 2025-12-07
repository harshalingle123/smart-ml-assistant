import uvicorn
import sys
import debugpy

if __name__ == "__main__":
    debugpy.listen(("0.0.0.0", 5678))
    print("🔥 FastAPI debugger listening on port 5678")

    sys.stdout = open("backend.log", "w")
    sys.stderr = open("backend.log", "a")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
