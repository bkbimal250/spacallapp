from rest_framework.views import exception_handler
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # If response is None, then there's an unhandled exception
    if response is None:
        if isinstance(exc, DjangoValidationError):
            data = {"error": "Validation Error", "details": exc.messages}
            return Response(data, status=400)
        
        # For other unhandled exceptions (like 500s)
        # We can log it here if needed
        data = {
            "error": "Internal Server Error",
            "details": str(exc) # Be careful exposing this in prod, maybe generic message
        }
        return Response(data, status=500)

    # If response is not None, we can standardize the structure
    # e.g. ensure "error" key exists
    if isinstance(response.data, dict):
        if 'detail' in response.data:
            response.data['error'] = response.data.pop('detail')
    
    return response
