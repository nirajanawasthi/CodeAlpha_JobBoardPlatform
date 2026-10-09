import django_filters
from .models import Job


class JobFilter(django_filters.FilterSet):
    location = django_filters.CharFilter(lookup_expr='icontains')
    category = django_filters.CharFilter(lookup_expr='icontains')
    min_salary = django_filters.NumberFilter(field_name='salary_max', lookup_expr='gte')
    max_salary = django_filters.NumberFilter(field_name='salary_min', lookup_expr='lte')
    company = django_filters.CharFilter(field_name='employer__company_name', lookup_expr='icontains')

    class Meta:
        model = Job
        fields = ['job_type', 'location', 'category', 'min_salary', 'max_salary', 'company']
