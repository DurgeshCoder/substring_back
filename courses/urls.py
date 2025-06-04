from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseCategoryViewSet, CourseViewSet, LessonViewSet

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'course-categories', CourseCategoryViewSet, basename='category')
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'lessons', LessonViewSet, basename='lesson')

# Include the router's URLs
urlpatterns = [
    path('', include(router.urls)),
]
