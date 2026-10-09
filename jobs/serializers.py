from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Application, Candidate, Employer, Job, Notification, Resume

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    def validate_username(self, v):
        if User.objects.filter(username=v).exists():
            raise serializers.ValidationError('Username already taken.')
        return v


class EmployerRegisterSerializer(RegisterSerializer):
    company_name = serializers.CharField()
    website = serializers.URLField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)


class CandidateRegisterSerializer(RegisterSerializer):
    phone = serializers.CharField(required=False, allow_blank=True)
    skills = serializers.CharField(required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)


class EmployerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer
        fields = ['id', 'company_name', 'website', 'description']


class JobSerializer(serializers.ModelSerializer):
    employer = EmployerSerializer(read_only=True)
    applications_count = serializers.IntegerField(source='applications.count', read_only=True)
    is_active = serializers.BooleanField(default=True)

    class Meta:
        model = Job
        fields = ['id', 'employer', 'title', 'description', 'category', 'location', 'job_type',
                  'salary_min', 'salary_max', 'deadline', 'is_active', 'created_at', 'applications_count']
        read_only_fields = ['created_at']

    def validate(self, data):
        lo, hi = data.get('salary_min'), data.get('salary_max')
        if lo and hi and lo > hi:
            raise serializers.ValidationError('salary_min cannot exceed salary_max.')
        return data


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['id', 'title', 'file', 'uploaded_at']
        read_only_fields = ['uploaded_at']


class ApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)
    candidate_name = serializers.CharField(source='candidate.__str__', read_only=True)
    resume_file = serializers.FileField(source='resume.file', read_only=True)

    class Meta:
        model = Application
        fields = ['id', 'job', 'job_title', 'candidate_name', 'resume', 'resume_file', 'cover_letter',
                  'status', 'applied_at', 'updated_at']
        read_only_fields = ['status', 'applied_at', 'updated_at']

    def validate(self, data):
        request = self.context['request']
        cand = request.user.candidate
        job = data['job']
        if not job.is_active:
            raise serializers.ValidationError('This job is closed.')
        if data['resume'].candidate_id != cand.id:
            raise serializers.ValidationError('Resume does not belong to you.')
        if Application.objects.filter(job=job, candidate=cand).exists():
            raise serializers.ValidationError('You already applied to this job.')
        return data


class StatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Application.Status.choices)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'message', 'is_read', 'created_at']
