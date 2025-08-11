# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubjectViewSet, TopicViewSet, ArticleViewSet

router = DefaultRouter()
router.register(r"subjects", SubjectViewSet, basename="subjects")
router.register(r"topics", TopicViewSet, basename="topics")
router.register(r"articles", ArticleViewSet, basename="articles")

urlpatterns = [
    path("api/", include(router.urls)),
]