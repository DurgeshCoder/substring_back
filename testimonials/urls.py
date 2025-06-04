from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TestimonialViewSet

# Create a router and register the TestimonialViewSet
router = DefaultRouter()
router.register(r'testimonials', TestimonialViewSet, basename='testimonial')

urlpatterns = [
    path('', include(router.urls)),  # Include the testimonial API endpoints
]
