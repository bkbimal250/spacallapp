from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginView, RequestOTPView, VerifyOTPView, UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    path("login/", LoginView.as_view()),
    path("otp/request/", RequestOTPView.as_view()),
    path("otp/verify/", VerifyOTPView.as_view()),
    path("", include(router.urls)),
]

