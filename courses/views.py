from django.db.models import Count, Prefetch
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import CourseCategory, Course, Lesson, Attachment
from .serializers import (
    CourseCategorySerializer,
    CourseSerializer,
    LessonSerializer,
    AttachmentSerializer,
    CourseCategorySerializer1
)

# Cache duration in seconds (1 hour)
CACHE_TTL = 60 * 60


class BaseViewSet(viewsets.ModelViewSet):
    """Base ViewSet with common functionality."""
    pass


class CourseCategoryViewSet(BaseViewSet):
    """ViewSet for CourseCategory model with optimized queries."""
    serializer_class = CourseCategorySerializer
    queryset = CourseCategory.objects.all()

    def get_queryset(self):
        """Optimize queryset based on action."""
        queryset = super().get_queryset()
        if self.action == 'list':
            queryset = queryset.prefetch_related(
                Prefetch(
                    'courses',
                    queryset=Course.objects.filter(is_published=True).only('id', 'title', 'slug', 'thumbnail')
                )
            )
        return queryset

    @action(detail=True, methods=['get'])
    def courses(self, request, pk=None):
        """Get published courses of a specific category."""
        category = self.get_object()
        courses = category.courses.filter(is_published=True).select_related('author')
        page = self.paginate_queryset(courses)
        if page is not None:
            serializer = CourseSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        
        serializer = CourseSerializer(
            courses,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    @method_decorator(cache_page(CACHE_TTL))
    @action(detail=False, methods=['get'], url_path="categories-with-courses")
    def categories_with_courses(self, request):
        """Get all categories with their published courses."""
        categories = self.get_queryset().prefetch_related(
            Prefetch(
                'courses',
                queryset=Course.objects.filter(is_published=True)
                .select_related('author')
                .only('id', 'title', 'slug', 'thumbnail', 'short_description', 'author')
            )
        )
        serializer = CourseCategorySerializer1(categories, many=True)
        return Response(serializer.data)


class CourseViewSet(BaseViewSet):
    """ViewSet for Course model with optimized queries."""
    serializer_class = CourseSerializer
    # lookup_field = 'slug'
    # lookup_url_kwarg = 'slug'

    def get_queryset(self):
        """Optimize queryset based on action."""
        queryset = Course.objects.filter(is_published=True).order_by('order')
        
        if self.action in ['retrieve', 'get_by_slug']:
            queryset = queryset.prefetch_related(
                Prefetch(
                    'lessons',
                    queryset=Lesson.objects.all().order_by('order')
                ),
                'attachments',
                'categories'
            ).select_related('author')
            
        return queryset.annotate(lesson_count=Count('lessons'))

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a course instance by ID."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='slug/(?P<slug>[^/.]+)')
    def get_by_slug(self, request, slug=None):
        """Get course details by slug."""
        try:
            course = self.get_queryset().get(slug=slug)
        except Course.DoesNotExist:
            return Response(
                {'detail': 'Course not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(course)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def lessons(self, request, pk=None):
        """Get lessons of a specific course."""
        course = self.get_object()
        lessons = course.lessons.all().order_by('order')
        page = self.paginate_queryset(lessons)
        if page is not None:
            serializer = LessonSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = LessonSerializer(lessons, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def attachments(self, request, pk=None):
        """Get attachments of a specific course."""
        course = self.get_object()
        attachments = course.attachments.all()
        page = self.paginate_queryset(attachments)
        if page is not None:
            serializer = AttachmentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = AttachmentSerializer(attachments, many=True)
        return Response(serializer.data)


class LessonViewSet(BaseViewSet):
    """ViewSet for Lesson model with optimized queries."""
    serializer_class = LessonSerializer
    
    def get_queryset(self):
        """Optimize queryset with prefetch_related for attachments."""
        return Lesson.objects.prefetch_related(
            Prefetch(
                'attachments',
                queryset=Attachment.objects.all().order_by('id')
            )
        )

    @action(detail=True, methods=['get'])
    def attachments(self, request, pk=None):
        """Get attachments of a specific lesson."""
        lesson = self.get_object()
        attachments = lesson.attachments.all()
        page = self.paginate_queryset(attachments)
        if page is not None:
            serializer = AttachmentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = AttachmentSerializer(attachments, many=True)
        return Response(serializer.data)


class AttachmentViewSet(BaseViewSet):
    """ViewSet for Attachment model."""
    serializer_class = AttachmentSerializer
    queryset = Attachment.objects.all()
