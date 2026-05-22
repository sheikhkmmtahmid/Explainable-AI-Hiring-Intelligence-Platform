from rest_framework import generics, permissions, status
from rest_framework.response import Response
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

    def perform_create(self, serializer):
        # Task 9: without authentication, new user gets default role = candidate (employee)
        serializer.save(role=User.Role.CANDIDATE)


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


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
    Task 7 & 8: Admin can create admin/recruiter/candidate.
    Manager (recruiter) can create recruiter/candidate only.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        actor = request.user
        if actor.role == User.Role.ADMIN:
            serializer = AdminCreateUserSerializer(data=request.data)
        elif actor.role == User.Role.RECRUITER:
            serializer = ManagerCreateUserSerializer(data=request.data)
        else:
            return Response(
                {"detail": "You do not have permission to create users."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserListView(APIView):
    """Admin and managers can list all users (for task assignment dropdowns)."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role not in (User.Role.ADMIN, User.Role.RECRUITER):
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
        users = User.objects.all().order_by("username")
        return Response(UserSerializer(users, many=True).data)
