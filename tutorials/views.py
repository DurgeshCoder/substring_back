from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets
from .models import TutorialCategory, Subject, Topic
from .serializers import TutorialCategorySerializer, SubjectSerializer, TopicSerializer


class TutorialCategoryViewSet(viewsets.ModelViewSet):
    queryset = TutorialCategory.objects.prefetch_related('subjects')
    serializer_class = TutorialCategorySerializer

    @action(detail=True, methods=['get'])
    def subjects(self, request, pk=None):
        """
        Get subjects under a specific category
        """
        category = self.get_object()
        subjects = category.subjects.all()
        serializer = SubjectSerializer(subjects, many=True)
        return Response(serializer.data)


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.prefetch_related('topics', 'categories')
    serializer_class = SubjectSerializer

    @action(detail=True, methods=['get'])
    def topics(self, request, pk=None):
        """
        Get topics under a specific subject
        """
        subject = self.get_object()
        topics = subject.topics.all()
        serializer = TopicSerializer(topics, many=True)
        return Response(serializer.data)


class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.select_related('subject')
    serializer_class = TopicSerializer
