from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import User
from .serializers import (
    AdminCreateUserSerializer,
    CustomTokenObtainPairSerializer,
    ManagerCreateUserSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)


class RegisterView(generics.CreateAPIView):
    """Public registration — always creates a Candidate (employee) account."""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_register"

    def perform_create(self, serializer):
        # Task 9: without authentication, new user gets default role = candidate (employee)
        serializer.save(role=User.Role.CANDIDATE)


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({"detail": "Token is invalid or already blacklisted."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_password_change"

    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not user.check_password(old_password):
            return Response(
                {"detail": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password updated successfully."})


class CreateUserView(APIView):
    """
    Platform staff (is_superuser) can create a user for any organization
    (or a brand new one). An org admin/recruiter can only create
    recruiter/candidate accounts inside their OWN organization -- the
    organization is never taken from the request body for that path, it's
    forced server-side from actor.organization so one company can never
    add a user into another company's account.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        actor = request.user
        if actor.is_platform_staff:
            serializer = AdminCreateUserSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
        elif actor.role in (User.Role.ADMIN, User.Role.RECRUITER):
            if actor.organization_id is None:
                return Response(
                    {"detail": "Your account isn't linked to an organization yet."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = ManagerCreateUserSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save(organization=actor.organization)
        else:
            return Response(
                {"detail": "You do not have permission to create users."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserListView(APIView):
    """Admin and managers can list users in their own organization (for task
    assignment dropdowns) -- platform staff can see everyone."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.is_platform_staff:
            users = User.objects.all().order_by("username")
        elif user.role in (User.Role.ADMIN, User.Role.RECRUITER):
            users = User.objects.filter(organization=user.organization).order_by("username")
        else:
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
        return Response(UserSerializer(users, many=True).data)
