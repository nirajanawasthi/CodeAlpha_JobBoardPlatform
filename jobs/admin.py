from django.contrib import admin
from .models import Application, Candidate, Employer, Job, Notification, Resume


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'employer', 'location', 'job_type', 'is_active', 'created_at')
    list_filter = ('job_type', 'is_active', 'location')
    search_fields = ('title', 'employer__company_name')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'job', 'status', 'applied_at')
    list_filter = ('status',)


admin.site.register([Employer, Candidate, Resume, Notification])
