"""
Logging Middleware for request/response tracking
"""
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses
    Tracks request duration and status codes
    """

    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()

        # Get request info
        method = request.method
        url = request.url.path
        client_host = request.client.host if request.client else "unknown"

        # Process request
        try:
            response: Response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log the request
            logger.info(
                f"{method} {url} - Status: {response.status_code} - "
                f"Duration: {duration:.3f}s - Client: {client_host}"
            )

            return response

        except Exception as e:
            # Log the error
            duration = time.time() - start_time
            logger.error(
                f"{method} {url} - Error: {str(e)} - "
                f"Duration: {duration:.3f}s - Client: {client_host}"
            )
            raise
