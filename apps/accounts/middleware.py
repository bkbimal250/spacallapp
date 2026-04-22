from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except Exception:
        return AnonymousUser()

class JWTAuthMiddleware:
    """
    Custom JWT Authentication Middleware for Channels.
    Expects token in query string: /ws/.../?token=TOKEN
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Close old database connections to prevent usage of timed out connections
        # close_old_connections() # Add if needed, usually Channels handles this

        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]

        print("🔥 TOKEN:", token)

        if token:
            try:
                access_token = AccessToken(token)
                # Note: access_token.payload might be validated here implicitly
                user_id = access_token.payload.get("user_id")
                
                print("✅ PAYLOAD:", access_token.payload)
                print("👉 USER_ID:", user_id)

                if user_id:
                    scope["user"] = await get_user(user_id)
                else:
                    scope["user"] = AnonymousUser()

            except Exception as e:
                print("❌ JWT ERROR:", str(e))
                scope["user"] = AnonymousUser()
        else:
            print("❌ No token")
            scope["user"] = AnonymousUser()

        return await self.inner(scope, receive, send)