from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('jobs', views.JobViewSet, basename='job')
router.register('resumes', views.ResumeViewSet, basename='resume')
router.register('applications', views.ApplicationViewSet, basename='application')
router.register('notifications', views.NotificationViewSet, basename='notification')

urlpatterns = [
    path('register/employer/', views.register_employer),
    path('register/candidate/', views.register_candidate),
    path('login/', obtain_auth_token),
    path('me/', views.me),
    path('admin/stats/', views.stats),
    path('', include(router.urls)),
]
