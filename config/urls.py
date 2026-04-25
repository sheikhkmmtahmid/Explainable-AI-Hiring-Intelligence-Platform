from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

api_v1_patterns = [
    path("auth/", include("apps.accounts.urls")),
    path("candidates/", include("apps.candidates.urls")),
    path("jobs/", include("apps.jobs.urls")),
    path("applications/", include("apps.applications.urls")),
    path("matching/", include("apps.matching.urls")),
    path("explainability/", include("apps.explainability.urls")),
    path("fairness/", include("apps.fairness.urls")),
    path("ingestion/", include("apps.ingestion.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("taxonomy/", include("apps.taxonomy.urls")),
    path("synthetic/", include("apps.synthetic_data.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1_patterns)),
    re_path(r"^.*$", TemplateView.as_view(template_name="index.html")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    try:
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass
