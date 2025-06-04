from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TutorialCategoryViewSet, SubjectViewSet, TopicViewSet

router = DefaultRouter()
router.register(r'tutorial-categories', TutorialCategoryViewSet, basename='tutorial-category')
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'topics', TopicViewSet, basename='topic')

urlpatterns = [
    path('', include(router.urls)),
]
