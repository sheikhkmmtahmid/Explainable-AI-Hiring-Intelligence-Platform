from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import JobPostViewSet

router = DefaultRouter()
router.register("", JobPostViewSet, basename="job")

urlpatterns = [path("", include(router.urls))]
