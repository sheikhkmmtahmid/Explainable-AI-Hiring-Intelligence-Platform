import django_filters

from .models import JobPost


class JobPostFilter(django_filters.FilterSet):
    country = django_filters.CharFilter(lookup_expr="icontains")
    city = django_filters.CharFilter(lookup_expr="icontains")
    industry = django_filters.CharFilter(lookup_expr="icontains")
    min_salary = django_filters.NumberFilter(field_name="salary_min", lookup_expr="gte")
    max_salary = django_filters.NumberFilter(field_name="salary_max", lookup_expr="lte")

    class Meta:
        model = JobPost
        fields = [
            "status", "employment_type", "experience_level",
            "work_model", "source", "is_synthetic",
        ]
