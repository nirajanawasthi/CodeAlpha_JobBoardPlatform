from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, ProtectedError
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .filters import JobFilter
from .models import Application, Candidate, Employer, Job, Notification, Resume
from .permissions import IsCandidate, IsEmployer
from .serializers import (ApplicationSerializer, CandidateRegisterSerializer, EmployerRegisterSerializer,
                          JobSerializer, NotificationSerializer, ResumeSerializer, StatusSerializer)

User = get_user_model()


def _create_user(d):
    return User.objects.create_user(username=d['username'], email=d['email'], password=d['password'],
                                    first_name=d.get('first_name', ''), last_name=d.get('last_name', ''))


@api_view(['POST'])
@permission_classes([AllowAny])
@transaction.atomic
def register_employer(request):
    s = EmployerRegisterSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    d = s.validated_data
    user = _create_user(d)
    Employer.objects.create(user=user, company_name=d['company_name'],
                            website=d.get('website', ''), description=d.get('description', ''))
    return Response({'token': Token.objects.create(user=user).key, 'role': 'employer'}, status=201)


@api_view(['POST'])
@permission_classes([AllowAny])
@transaction.atomic
def register_candidate(request):
    s = CandidateRegisterSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    d = s.validated_data
    user = _create_user(d)
    Candidate.objects.create(user=user, phone=d.get('phone', ''), skills=d.get('skills', ''), bio=d.get('bio', ''))
    return Response({'token': Token.objects.create(user=user).key, 'role': 'candidate'}, status=201)


class JobViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    filterset_class = JobFilter
    search_fields = ['title', 'description', 'employer__company_name', 'category']
    ordering_fields = ['created_at', 'salary_min', 'salary_max', 'deadline']

    def get_queryset(self):
        qs = Job.objects.select_related('employer')
        user = self.request.user
        if self.action == 'my_jobs':
            return qs.filter(employer__user=user)
        if self.action in ('list', 'retrieve'):
            return qs.filter(is_active=True)
        return qs.filter(employer__user=user)  # write ops only on own jobs

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsEmployer()]

    def perform_create(self, serializer):
        serializer.save(employer=self.request.user.employer)

    @action(detail=False, methods=['get'])
    def my_jobs(self, request):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        return self.get_paginated_response(self.get_serializer(page, many=True).data)

    @action(detail=True, methods=['get'])
    def applications(self, request, pk=None):
        job = self.get_object()
        qs = job.applications.select_related('candidate__user', 'job')
        return Response(ApplicationSerializer(qs, many=True, context={'request': request}).data)


class ResumeViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                    mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = ResumeSerializer
    permission_classes = [IsCandidate]

    def get_queryset(self):
        return Resume.objects.filter(candidate=self.request.user.candidate)

    def perform_create(self, serializer):
        serializer.save(candidate=self.request.user.candidate)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response({'detail': 'This resume is used in an application and cannot be deleted.'},
                            status=status.HTTP_400_BAD_REQUEST)


class ApplicationViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                         viewsets.GenericViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'job']

    def get_queryset(self):
        u = self.request.user
        qs = Application.objects.select_related('job', 'candidate__user')
        if hasattr(u, 'employer'):
            return qs.filter(job__employer=u.employer)
        if hasattr(u, 'candidate'):
            return qs.filter(candidate=u.candidate)
        return qs.none()

    def get_permissions(self):
        if self.action == 'create':
            return [IsCandidate()]
        if self.action == 'set_status':
            return [IsEmployer()]
        return super().get_permissions()

    def perform_create(self, serializer):
        app = serializer.save(candidate=self.request.user.candidate)
        Notification.objects.create(
            user=app.job.employer.user,
            message=f'New application from {app.candidate} for "{app.job.title}".')

    @action(detail=True, methods=['patch'], url_path='status')
    def set_status(self, request, pk=None):
        app = self.get_object()  # scoped to this employer's jobs
        s = StatusSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        app.status = s.validated_data['status']
        app.save(update_fields=['status', 'updated_at'])
        Notification.objects.create(
            user=app.candidate.user,
            message=f'Your application for "{app.job.title}" is now: {app.get_status_display()}.')
        return Response(ApplicationSerializer(app, context={'request': request}).data)


class NotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_read']

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response({'detail': 'ok'})


@api_view(['GET'])
@permission_classes([IsAdminUser])
def stats(request):
    by_status = dict(Application.objects.values_list('status').annotate(c=Count('id')))
    top_jobs = (Job.objects.annotate(c=Count('applications')).order_by('-c')[:5]
                .values('id', 'title', 'c'))
    return Response({
        'users': User.objects.count(),
        'employers': Employer.objects.count(),
        'candidates': Candidate.objects.count(),
        'jobs': Job.objects.count(),
        'active_jobs': Job.objects.filter(is_active=True).count(),
        'applications': Application.objects.count(),
        'applications_by_status': by_status,
        'top_jobs': list(top_jobs),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    u = request.user
    role = 'employer' if hasattr(u, 'employer') else 'candidate' if hasattr(u, 'candidate') else 'user'
    return Response({'username': u.username, 'role': role, 'is_staff': u.is_staff})
