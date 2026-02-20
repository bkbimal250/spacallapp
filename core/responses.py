from rest_framework.response import Response


def success_response(data=None, message="Success", status=200):
    return Response(
        {
            "status": True,
            "message": message,
            "data": data,
        },
        status=status,
    )


def error_response(message="Error", status=400):
    return Response(
        {
            "status": False,
            "message": message,
        },
        status=status,
    )
