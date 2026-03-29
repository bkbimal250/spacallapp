from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()

class JWTAuthMiddleware:
    """
    Custom middleware for Django Channels to authenticate via JWT token 
    passed in the query string (e.g., ws://.../?token=<token>).
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Close old database connections to prevent issues with long-running processes
        # from django.db import close_old_connections
        # close_old_connections()

        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]

        if token:
            try:
                # Validate the token using SimpleJWT's AccessToken class
                access_token = AccessToken(token)
                user_id = access_token.payload.get("user_id")
                
                # Fetch the user from the database and attach to the scope
                scope["user"] = await get_user(user_id)
            except Exception as e:
                print(f"JWT Auth Error: {e}")
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await self.inner(scope, receive, send)

def JWTAuthMiddlewareStack(inner):
    """
    Helper function to wrap the middleware stack.
    """
    return JWTAuthMiddleware(inner)
