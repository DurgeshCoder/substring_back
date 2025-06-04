from django.db.models import Count
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import CourseCategory, Course, Lesson, Attachment
from .serializers import (
    CourseCategorySerializer,
    CourseSerializer,
    LessonSerializer,
    AttachmentSerializer, CourseCategorySerializer1
)


# Course Category ViewSet
class CourseCategoryViewSet(viewsets.ModelViewSet):
    queryset = CourseCategory.objects.prefetch_related('courses')
    serializer_class = CourseCategorySerializer

    @action(detail=True, methods=['get'])
    def courses(self, request, pk=None):
        """
        Get courses of a specific category
        """
        category = self.get_object()
        print(category)
        courses = category.courses.all()
        serializer = CourseSerializer(courses, many=True, context={'request': request})
        print(serializer.data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path="categories-with-courses")
    def categories_with_courses(self, request, pk=None):
        print("courses with categories")
        categories_with_courses = CourseCategory.objects.prefetch_related('courses').all()
        serializer = CourseCategorySerializer1(categories_with_courses, many=True)
        return JsonResponse(serializer.data, safe=False)


# Course ViewSet
class CourseViewSet(viewsets.ModelViewSet):
    # queryset = Course.objects.prefetch_related('lessons', 'attachments').annotate(lesson_count=Count('lessons'))
    """
    ViewSet for Course model.
    """
    serializer_class = CourseSerializer  # Replace with your actual serializer

    # Replace with your actual serializer

    def get_queryset(self):
        """
        Customize the queryset based on the action (list or retrieve).
        """
        if self.action == 'list':
            # Exclude lessons and attachments for list view
            return Course.objects.annotate(lesson_count=Count('lessons')).filter(is_published=True).order_by('order')
        elif self.action == 'retrieve':
            # Include lessons and attachments for retrieve view
            return Course.objects.prefetch_related('lessons', 'attachments', 'categories').annotate(
                lesson_count=Count('lessons')
            )

        # Default fallback
        return Course.objects.all().filter(is_published=True).order_by("order")

    @action(detail=False, methods=['get'], url_path='slug/(?P<slug>[^/.]+)')
    def get_by_slug(self, request, slug=None):
        """Get course details by slug"""
        try:
            course = Course.objects.prefetch_related('lessons', 'attachments').get(slug=slug)
        except Course.DoesNotExist:
            return Response({'detail': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(course)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def lessons(self, request, pk=None):
        """
        Get lessons of a specific course
        """
        course = self.get_object()
        lessons = course.lessons.all()
        serializer = LessonSerializer(lessons, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def attachments(self, request, pk=None):
        """
        Get attachments of a specific course
        """
        course = self.get_object()
        attachments = course.attachments.all()
        serializer = AttachmentSerializer(attachments, many=True)
        return Response(serializer.data)


# Lesson ViewSet
class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.prefetch_related('attachments')
    serializer_class = LessonSerializer

    @action(detail=True, methods=['get'])
    def attachments(self, request, pk=None):
        """
        Get attachments of a specific lesson
        """
        lesson = self.get_object()
        attachments = lesson.attachments.all()
        serializer = AttachmentSerializer(attachments, many=True)
        return Response(serializer.data)


# Attachment ViewSet
class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
