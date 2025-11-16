"""
Middleware to handle request size limits
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.config import settings


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce request size limits
    """
    async def dispatch(self, request: Request, call_next):
        # Check content length header
        content_length = request.headers.get("content-length")

        if content_length:
            content_length = int(content_length)
            max_size = settings.MAX_UPLOAD_SIZE

            if content_length > max_size:
                size_mb = content_length / (1024 * 1024)
                max_mb = max_size / (1024 * 1024)
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": f"Request body too large ({size_mb:.2f} MB). Maximum allowed size is {max_mb:.0f} MB."
                    }
                )

        response = await call_next(request)
        return response
