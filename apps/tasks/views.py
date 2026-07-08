from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Task
from .serializers import TaskSerializer

# Role constants (mapped from the project's existing User.Role choices)
MANAGER_ROLES = ("admin", "recruiter")   # can delete, update title, assign tasks
EMPLOYEE_ROLES = ("candidate",)           # can create own task, update description only


class TaskViewSet(ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        base = Task.objects.select_related("created_by", "assigned_to")
        if user.is_platform_staff:
            return base.all()
        if user.role in MANAGER_ROLES:
            # managers/admins see every task within their own company --
            # never another organization's internal task list.
            return base.filter(created_by__organization_id=user.organization_id)
        # employees see only tasks they created or were assigned to them
        return base.filter(created_by=user) | base.filter(assigned_to=user)

    def perform_create(self, serializer):
        user = self.request.user
        if user.role in EMPLOYEE_ROLES:
            # Employee always owns the task; cannot assign to others
            serializer.save(created_by=user, assigned_to=user)
        else:
            serializer.save(created_by=user)

    def partial_update(self, request, *args, **kwargs):
        task = self.get_object()
        user = request.user
        data = request.data.copy()

        # Employees cannot change the title
        if user.role in EMPLOYEE_ROLES and "title" in data:
            return Response(
                {"detail": "Employees can only update the task description."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(task, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        # Force all PUT/PATCH through partial_update logic
        kwargs["partial"] = True
        return self.partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        user = request.user
        if user.role not in MANAGER_ROLES:
            return Response(
                {"detail": "Only managers can delete tasks."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)
