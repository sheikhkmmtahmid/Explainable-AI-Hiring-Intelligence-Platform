from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    ChangePasswordView,
    CreateUserView,
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
    UserListView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    # Task 7 & 8: admin/manager user creation
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/create/", CreateUserView.as_view(), name="user-create"),
]
