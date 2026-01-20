"""
Security headers middleware for enhanced application security.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all HTTP responses.
    
    Headers added:
    - X-Content-Type-Options: Prevents MIME type sniffing
    - X-Frame-Options: Prevents clickjacking attacks
    - X-XSS-Protection: Enables browser XSS protection
    - Strict-Transport-Security: Forces HTTPS connections
    - Content-Security-Policy: Controls resource loading
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Controls browser features
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process request and add security headers to response."""
        response: Response = await call_next(request)
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Enable XSS protection (legacy, but still useful for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Force HTTPS in production (31536000 = 1 year)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy - restrict resource loading
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )
        
        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Control browser features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )
        
        return response
