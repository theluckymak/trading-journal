"""
Request ID tracking middleware for request tracing and debugging.
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import contextvars


# Context variable to store request ID across async operations
request_id_var = contextvars.ContextVar('request_id', default=None)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Add unique request ID to each request for tracing.
    
    Request ID is:
    - Generated as UUID4
    - Added to response headers as X-Request-ID
    - Stored in context for access in request handlers
    - Useful for log correlation and debugging
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process request and add request ID."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Store in context var for access throughout request lifecycle
        request_id_var.set(request_id)
        
        # Also attach to request state
        request.state.request_id = request_id
        
        # Process request
        response: Response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


def get_request_id() -> str:
    """Get current request ID from context."""
    return request_id_var.get()
