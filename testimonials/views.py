from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets
from .models import Testimonial
from .serializers import TestimonialSerializer


class TestimonialViewSet(viewsets.ModelViewSet):
    """
    A viewset for managing testimonials.
    """
    queryset = Testimonial.objects.all().order_by('-created_at')
    serializer_class = TestimonialSerializer

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Get featured testimonials.
        """
        featured_testimonials = Testimonial.objects.filter(is_featured=True)
        serializer = self.get_serializer(featured_testimonials, many=True)
        return Response(serializer.data)
