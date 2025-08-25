# views.py
from __future__ import annotations

from django.db.models import Prefetch, Count
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
class SubjectViewSet(viewsets.ModelViewSet):
    """
    /api/subjects/                (GET list, POST create)
    /api/subjects/<slug>/         (GET retrieve, PATCH/PUT, DELETE)
    """
    lookup_field = "slug"  # match your URL docs; avoids extra PK lookups
    permission_classes = [ReadOnlyOrStaff]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["visibility", "is_active", "is_featured"]
    search_fields = ["name", "slug", "tagline", "description", "meta_title", "meta_description"]
    ordering_fields = ["position", "name", "created_at", "updated_at"]

    def get_queryset(self):
        base_qs = Subject.objects.all().order_by("position", "name")

        # Keep column set lean for list
        if self.action == "list":
            qs = base_qs.only(
                "id", "slug", "name", "tagline", "position", "is_active", "is_featured"
            ).annotate(topic_count=Count("topics"))
            # Light prefetch: just what's needed by TopicMiniSerializer (id, slug, name, position)
            qs = qs.prefetch_related(
                Prefetch(
                    "topics",
                    queryset=Topic.objects.only("id", "slug", "name", "position", "subject_id")
                    .filter(is_active=True)
                    .order_by("position", "name"),
                )
            )
            return qs

        # For retrieve and custom "full" action, load a bit more
        if self.action in {"retrieve", "full"}:
            qs = base_qs.only(
                "id", "slug", "name", "tagline", "description",
                "meta_title", "meta_description", "position", "is_active", "is_featured"
            )
            # Prefetch topics (and optionally their articles for "full", see action below)
            qs = qs.prefetch_related(
                Prefetch(
                    "topics",
                    queryset=Topic.objects.select_related("subject")
                    .only("id", "slug", "name", "summary", "position", "is_active", "subject_id")
                    .order_by("position", "name"),
                )
            )
            return qs

        # Writes / other actions – no heavy prefetch
        return base_qs

    def get_serializer_class(self):
        return SubjectDetailSerializer if self.action == "retrieve" else SubjectListSerializer

    @action(detail=True, methods=["get"])
    def topics(self, request, slug=None):
        """GET /api/subjects/<slug>/topics/ — list topics under a subject."""
        subject = self.get_object()
        qs = (
            subject.topics.only("id", "slug", "name", "position", "is_active", "subject_id")
            .filter(is_active=True)
            .order_by("position", "name")
        )
        serializer = TopicMiniSerializer(qs, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="with-topics-and-articles")
    def full(self, request, slug=None):
        """
        GET /api/subjects/<slug>/with-topics-and-articles
        Loads subject -> topics -> articles (with author) efficiently.
        """
        # Re-fetch current object with deeper prefetch for this endpoint
        subject = (
            Subject.objects.filter(pk=self.get_object().pk)
            .prefetch_related(
                Prefetch(
                    "topics",
                    queryset=Topic.objects.only(
                        "id", "slug", "name", "summary", "position", "is_active", "subject_id"
                    ).prefetch_related(
                        Prefetch(
                            "articles",
                            queryset=Article.objects.select_related("author", "topic", "topic__subject")
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
    lookup_field = "slug"
    permission_classes = [ReadOnlyOrStaff]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_active", "subject"]
    search_fields = ["name", "slug", "summary", ]
    ordering_fields = ["position", "name", "created_at", "updated_at"]

    def get_queryset(self):
        base = Topic.objects.select_related("subject").order_by(
            "subject__position", "position", "name"
        )

        # Friendly filter by subject slug if provided
        subject_slug = self.request.query_params.get("subject") or self.kwargs.get("subject_slug")
        if subject_slug:
            base = base.filter(subject__slug=subject_slug)

        if self.action == "list":
            return base.only(
                "id", "slug", "name", "summary", "position", "is_active", "subject_id"
            )
        # retrieve
        return base.only(
            "id", "slug", "name", "summary", "position", "is_active", "subject_id",

        )

    def get_serializer_class(self):
        print("getting topic serializer")
        print(self.action)
        return TopicDetailSerializer if self.action == "retrieve" else TopicListSerializer

    @action(detail=True, methods=["get"])
    def articles(self, request, slug=None):
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
    lookup_field = "slug"
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "difficulty", "is_featured", "topic"]
    search_fields = ["title", "slug", "excerpt", "content_html", "meta_title", "meta_description"]
    ordering_fields = ["order_in_topic", "published_at", "created_at", "updated_at", "views", "likes"]

    def get_queryset(self):
        base = (
            Article.objects.select_related("topic", "topic__subject", "author")
            .order_by("topic__position", "order_in_topic", "-published_at", "title")
        )

        # Friendly filters by slugs
        subject_slug = self.request.query_params.get("subject") or self.kwargs.get("subject_slug")
        if subject_slug:
            base = base.filter(topic__subject__slug=subject_slug)

        topic_slug = self.request.query_params.get("topic") or self.kwargs.get("topic_slug")
        if topic_slug:
            base = base.filter(topic__slug=topic_slug)

        featured = self.request.query_params.get("featured")
        if featured in ("true", "1", "yes"):
            base = base.filter(is_featured=True)

        # Narrow columns: list vs retrieve
        if self.action == "list":
            return base.only(
                "id", "slug", "title", "excerpt", "order_in_topic",
                "published_at", "status", "difficulty", "is_featured",
                "views", "likes",
                "topic_id", "author_id"
            )
        # retrieve
        return base.only(
            "id", "slug", "title", "excerpt", "content_html",
            "order_in_topic", "published_at", "created_at", "updated_at",
            "status", "difficulty", "is_featured", "views", "likes",
            "meta_title", "meta_description",
            "topic_id", "author_id"
        )

    def get_serializer_class(self):
        return ArticleDetailSerializer if self.action == "retrieve" else ArticleListSerializer
