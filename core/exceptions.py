from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    """
    Standardize all API error responses.
    """
    response = exception_handler(exc, context)

    if response is not None:
        custom_response_data = {
            'success': False,
            'error': {
                'code': getattr(exc, 'default_code', 'error'),
                'message': str(exc),
                'details': response.data
            }
        }
        response.data = custom_response_data
    else:
        # Handle unexpected exceptions
        # In production, this should be logged to Sentry or similar
        return Response({
            'success': False,
            'error': {
                'code': 'server_error',
                'message': 'An unexpected error occurred.',
                'details': None
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response
