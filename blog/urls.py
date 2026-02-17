from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import BlogViewSet, CategoryViewSet, AuthorViewSet

router = DefaultRouter()
router.register('blogs', BlogViewSet, basename='blog')
router.register('blog-categories', CategoryViewSet, basename='category')

router.register('authors', AuthorViewSet, basename='author')
urlpatterns = [
    path('', include(router.urls)),  # Include DRF routes
]
