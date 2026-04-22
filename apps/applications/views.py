from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Application, ApplicationNote, InterviewSlot
from .serializers import ApplicationNoteSerializer, ApplicationSerializer, InterviewSlotSerializer


class ApplicationViewSet(ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Application.objects.select_related("candidate", "job")
        if user.role == "candidate":
            return qs.filter(candidate__user=user)
        return qs

    @action(detail=True, methods=["patch"])
    def update_status(self, request, pk=None):
        application = self.get_object()
        new_status = request.data.get("status")
        if new_status not in Application.Status.values:
            return Response({"detail": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)
        application.status = new_status
        application.reviewed_by = request.user
        application.reviewed_at = timezone.now()
        application.save(update_fields=["status", "reviewed_by", "reviewed_at"])
        return Response(ApplicationSerializer(application).data)

    @action(detail=True, methods=["post"])
    def add_note(self, request, pk=None):
        application = self.get_object()
        serializer = ApplicationNoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(application=application, author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def schedule_interview(self, request, pk=None):
        application = self.get_object()
        serializer = InterviewSlotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(application=application)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
