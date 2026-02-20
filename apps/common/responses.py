from rest_framework.response import Response


def success_response(data=None, message="Success", status_code=200):
    return Response(
        {"status": True, "message": message, "data": data}, status=status_code
    )


def error_response(message="Error", errors=None, status_code=400):
    return Response(
        {"status": False, "message": message, "errors": errors}, status=status_code
    )

def api_success(data=None):
    return Response({
        "success": True,
        "data": data,
    })


def api_error(message):
    return Response({
        "success": False,
        "error": message,
    })
