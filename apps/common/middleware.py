import uuid
from typing import Any, Callable
import structlog
from django.http import HttpRequest, HttpResponse

logger = structlog.get_logger(__name__)

class CorrelationIdMiddleware:
    """
    Middleware that ensures every incoming request has a unique Correlation ID.
    If the client provides 'X-Correlation-ID' in headers, we use it (useful for tracing across microservices).
    Otherwise, we generate a fresh UUID.
    This ID is bound to the structlog context so all subsequent logs for this request include it.
    """
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Check if the header was provided by an upstream proxy or client
        correlation_id = request.headers.get('X-Correlation-ID')
        
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
            
        # Bind the correlation_id to the structlog thread-local context
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            request_path=request.path,
            method=request.method,
            user_id=str(request.user.id) if request.user.is_authenticated else "anonymous"
        )
        
        logger.info("Request started")
        
        response = self.get_response(request)
        
        # Inject it into the response headers so clients can trace it
        response['X-Correlation-ID'] = correlation_id
        
        logger.info("Request completed", status_code=response.status_code)
        
        # Clear context vars so they don't leak into the next request on this thread
        structlog.contextvars.clear_contextvars()
        
        return response
