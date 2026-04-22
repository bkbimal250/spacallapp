from urllib.parse import parse_qs
from uuid import UUID
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

@database_sync_to_async
def get_user(user_id):
    try:
        user = User.objects.get(id=user_id)
        print(f"👤 USER FOUND: {user.email} (Role: {user.role})")
        return user
    except User.DoesNotExist:
        print(f"❌ USER NOT FOUND: id={user_id}")
        return AnonymousUser()
    except Exception as e:
        print(f"❌ DB ERROR in get_user: {str(e)}")
        return AnonymousUser()

class JWTAuthMiddleware:
    """
    Custom JWT Authentication Middleware for Channels.
    Expects token in query string: /ws/.../?token=TOKEN
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]

        if token:
            try:
                # This validates the token (expiration, signature, etc.)
                access_token = AccessToken(token)
                
                # Support multiple user_id keys for different JWT configurations
                raw_user_id = (
                    access_token.payload.get("user_id") or 
                    access_token.payload.get("id") or 
                    access_token.payload.get("sub")
                )
                
                print(f"✅ JWT VALID. Raw User ID: {raw_user_id}")
                
                if raw_user_id:
                    try:
                        # CRITICAL: Convert string UUID to UUID object for strict DB engines (Postgres)
                        user_id = UUID(str(raw_user_id))
                        scope["user"] = await get_user(user_id)
                    except ValueError:
                        print(f"❌ UUID ERROR: Invalid format ({raw_user_id})")
                        scope["user"] = AnonymousUser()
                else:
                    print("❌ JWT ERROR: No user identifier in payload")
                    scope["user"] = AnonymousUser()

            except Exception as e:
                print(f"❌ JWT VALIDATION FAILED: {str(e)}")
                scope["user"] = AnonymousUser()
        else:
            print("⚠️ WebSocket attempt WITHOUT token")
            scope["user"] = AnonymousUser()

        return await self.inner(scope, receive, send)