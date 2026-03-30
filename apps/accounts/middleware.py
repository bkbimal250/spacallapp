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
    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        return JWTAuthMiddlewareInstance(scope, self.inner)


class JWTAuthMiddlewareInstance:
    def __init__(self, scope, inner):
        self.scope = scope
        self.inner = inner

    async def __call__(self, receive, send):
        query_string = self.scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]

        print("🔥 TOKEN:", token)

        if token:
            try:
                access_token = AccessToken(token)
                print("✅ PAYLOAD:", access_token.payload)

                user_id = access_token.payload.get("user_id")
                print("👉 USER_ID:", user_id)

                if user_id:
                    self.scope["user"] = await get_user(user_id)
                else:
                    self.scope["user"] = AnonymousUser()

            except Exception as e:
                print("❌ JWT ERROR:", str(e))
                self.scope["user"] = AnonymousUser()
        else:
            print("❌ No token")
            self.scope["user"] = AnonymousUser()

        inner = self.inner(self.scope)
        return await inner(receive, send)