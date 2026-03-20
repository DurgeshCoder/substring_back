# views.py
from __future__ import annotations

from django.db.models import Prefetch, Count
from django.shortcuts import get_object_or_404
from jinja2.utils import consume
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Subject, Topic, Article

from .serializers import (
    SubjectListSerializer, SubjectDetailSerializer,
    TopicListSerializer, TopicDetailSerializer, TopicMiniSerializer,
    ArticleListSerializer, ArticleDetailSerializer, SubjectWithTopicsSerializer)


# ---------- Permissions ----------
class ReadOnlyOrStaff(permissions.BasePermission):
    """Read for everyone; writes only for staff."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


# ---------- Subject ----------
class SubjectViewSet(viewsets.ModelViewSet):  # match your URL docs; avoids extra PK lookups
    permission_classes = [ReadOnlyOrStaff]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["visibility", "is_active", "is_featured"]
    search_fields = ["name", "slug", "tagline", "description", "meta_title", "meta_description"]
    ordering_fields = ["position", "name", "created_at", "updated_at"]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.is_staff:
            return Subject.objects.all().order_by(
                "-created_at")
        return Subject.objects.prefetch_related("topics").filter(is_active=True, visibility='public').order_by(
            "-created_at")

    def get_serializer_class(self):
        return SubjectDetailSerializer if self.action == "retrieve" else SubjectListSerializer

    @action(detail=True, methods=["get"])
    def topics(self, request, pk=None):
        """GET /api/subjects/<slug>/topics/ — list topics under a subject."""
        subject = self.get_object()
        qs = (
            subject.topics.only("id", "slug", "name", "position", "is_active", "subject_id")
            .filter(is_active=True)
            .order_by("position", "name")
        )
        serializer = TopicMiniSerializer(qs, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="slug/(?P<slug>[^/.]+)")
    def full(self, request, slug=None):
        """
        GET /api/subjects/<slug>/with-topics-and-articles
        Loads subject -> topics -> articles (with author) efficiently.
        """
        # Re-fetch current object with deeper prefetch for this endpoint
        subject = (
            Subject.objects.filter(slug=slug, is_active=True)
            .prefetch_related(
                Prefetch(
                    "topics",
                    queryset=Topic.objects.only(
                        "id", "slug", "name", "summary", "position", "is_active", "subject_id"
                    ).prefetch_related(
                        Prefetch(
                            "articles",
                            queryset=Article.objects
                            .only(
                                "id", "slug", "title", "excerpt", "order_in_topic",
                                "published_at", "is_featured", "topic_id", "author_id"
                            )
                            .order_by("order_in_topic", "-published_at", "title"),
                        )
                    ).order_by("position", "name"),
                )
            )
            .first()
        )
        serializer = SubjectWithTopicsSerializer(subject, context=self.get_serializer_context())
        return Response(serializer.data)


# ---------- Topic ----------
class TopicViewSet(viewsets.ModelViewSet):
    """
    /api/topics/                          (list/create)
    /api/topics/<slug>/                   (retrieve/update/delete)
    Tips:
      - Filter by subject via ?subject=<subject-slug>
    """

    permission_classes = [ReadOnlyOrStaff]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_active", "subject"]
    search_fields = ["name", "slug", "summary", ]
    ordering_fields = ["position", "name", "created_at", "updated_at"]

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return Topic.objects.select_related("subject").order_by(
                "-created_at"
                "-updated_at"
            )
        return Topic.objects.select_related("subject").filter(is_active=True).order_by("-created_at", "-updated_at")

    def get_serializer_class(self):
        return TopicDetailSerializer if self.action == "retrieve" else TopicListSerializer

    @action(detail=True, methods=["get"])
    def articles(self, request, pk=None):
        """GET /api/topics/<slug>/articles/ — list articles in this topic."""
        topic = self.get_object()
        qs = (
            topic.articles.select_related("topic", "topic__subject", "author")
            .only(
                "id", "slug", "title", "excerpt", "order_in_topic",
                "published_at", "status", "is_featured", "views", "likes",
                "topic_id", "author_id"
            )
            .order_by("order_in_topic", "-published_at", "title")
        )
        ser = ArticleListSerializer(qs, many=True, context=self.get_serializer_context())
        return Response(ser.data)


# ---------- Article ----------
class ArticleViewSet(viewsets.ModelViewSet):
    """
    /api/articles/                              (list/create)
    /api/articles/<pk>/                         (retrieve/update/delete)
    Filters:
      ?status=published
      ?subject=<subject-slug>
      ?topic=<topic-slug>
      ?featured=true
    """
    permission_classes = [ReadOnlyOrStaff]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "difficulty", "is_featured", "topic"]
    search_fields = ["title", "slug", "excerpt", "content_html", "meta_title", "meta_description"]
    ordering_fields = ["order_in_topic", "published_at", "created_at", "updated_at", "views", "likes"]

    # getting article by slug
    # /slug/<slug>
    @action(detail=False, methods=["get"], url_path="slug/(?P<slug>[^/.]+)")
    def by_slug(self, request, slug=None):
        article = get_object_or_404(
            self.get_queryset(),
            slug=slug,
        )

        serializer = ArticleDetailSerializer(article, context=self.get_serializer_context())
        return Response(serializer.data)

    def get_queryset(self):
        if self.request.user and self.request.user.is_staff:
            return Article.objects.select_related("topic", "topic__subject", "author").order_by("-published_at")
        return Article.objects.select_related("topic", "topic__subject", "author").filter(status="published").order_by(
            "-published_at")

    def get_serializer_class(self):
        return ArticleDetailSerializer if self.action == "retrieve" else ArticleListSerializer
