from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ApplicationViewSet

router = DefaultRouter()
router.register("", ApplicationViewSet, basename="application")

urlpatterns = [path("", include(router.urls))]
