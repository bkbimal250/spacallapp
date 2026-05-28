from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView,
    OnlineUsersView,
    RequestOTPView,
    RequestPhoneOTPView,
    UpdateProfileView,
    UserLoginHistoryViewSet,
    UserViewSet,
    VerifyOTPView,
    VerifyPhoneOTPView,
)

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"login-history", UserLoginHistoryViewSet, basename="login-history")

urlpatterns = [
    path("login/", LoginView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("otp/request/", RequestOTPView.as_view()),
    path("otp/verify/", VerifyOTPView.as_view()),
    path("otp/phone/request/", RequestPhoneOTPView.as_view()),
    path("otp/phone/verify/", VerifyPhoneOTPView.as_view()),
    path("users/online/", OnlineUsersView.as_view()),
    path("profile/", UpdateProfileView.as_view()),
    path("", include(router.urls)),
]

