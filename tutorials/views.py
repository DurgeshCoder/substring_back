# views.py
from __future__ import annotations

from rest_framework import viewsets, permissions, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Subject, Topic, Article
from .serializers import (
    SubjectListSerializer, SubjectDetailSerializer,
    TopicListSerializer, TopicDetailSerializer, TopicMiniSerializer,
    ArticleListSerializer, ArticleDetailSerializer, ArticleMiniSerializer,
)

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
    queryset = Subject.objects.all().order_by("position", "name")
    permission_classes = [ReadOnlyOrStaff]
    lookup_field = "slug"
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["visibility", "is_active", "is_featured"]
    search_fields = ["name", "slug", "tagline", "description", "meta_title", "meta_description"]
    ordering_fields = ["position", "name", "created_at", "updated_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        # Prefetch topics (mini) when listing or detailing
        if self.action in ("list", "retrieve"):
            qs = qs.prefetch_related("topics")
        return qs

    def get_serializer_class(self):
        return SubjectDetailSerializer if self.action == "retrieve" else SubjectListSerializer

    @action(detail=True, methods=["get"])
    def topics(self, request, slug=None):
        """GET /api/subjects/<slug>/topics/ — list topics under a subject."""
        subject = self.get_object()
        qs = subject.topics.all().order_by("position", "name")
        serializer = TopicMiniSerializer(qs, many=True, context=self.get_serializer_context())
        return Response(serializer.data)


# ---------- Topic ----------
class TopicViewSet(viewsets.ModelViewSet):
    """
    /api/topics/                          (list/create)
    /api/topics/<slug>/                   (retrieve/update/delete)  -- optionally scoped by ?subject=<subject-slug>
    Tips:
      - Filter by subject via ?subject=<subject-slug>
    """
    permission_classes = [ReadOnlyOrStaff]
    lookup_field = "slug"
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_active", "subject"]  # 'subject' accepts PK; see subject slug filter below
    search_fields = ["name", "slug", "summary", "meta_title", "meta_description"]
    ordering_fields = ["position", "name", "created_at", "updated_at"]

    def get_queryset(self):
        qs = Topic.objects.select_related("subject").order_by("subject__position", "position", "name")
        # Filter by subject slug if provided (friendly)
        subject_slug = self.request.query_params.get("subject") or self.kwargs.get("subject_slug")
        if subject_slug:
            qs = qs.filter(subject__slug=subject_slug)
        return qs

    def get_serializer_class(self):
        return TopicDetailSerializer if self.action == "retrieve" else TopicListSerializer

    @action(detail=True, methods=["get"])
    def articles(self, request, slug=None):
        """GET /api/topics/<slug>/articles/ — list articles in this topic."""
        topic = self.get_object()
        qs = (
            topic.articles.select_related("topic", "topic__subject", "author")
            .order_by("order_in_topic", "-published_at", "title")
        )
        ser = ArticleMiniSerializer(qs, many=True, context=self.get_serializer_context())
        return Response(ser.data)


# ---------- Article ----------
class ArticleViewSet(viewsets.ModelViewSet):
    """
    /api/articles/                              (list/create)
    /api/articles/<pk>/                         (retrieve/update/delete)  [lookup by ID]
    Filters:
      ?status=published
      ?subject=<subject-slug>
      ?topic=<topic-slug>
      ?featured=true
    """
    permission_classes = [ReadOnlyOrStaff]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    # Note: we keep PK lookups for Article by default (slugs are only unique within topic)
    filterset_fields = ["status", "difficulty", "is_featured", "topic"]  # 'topic' accepts PK
    search_fields = ["title", "slug", "excerpt", "content_html", "meta_title", "meta_description"]
    ordering_fields = ["order_in_topic", "published_at", "created_at", "updated_at", "views", "likes"]

    def get_queryset(self):
        qs = (
            Article.objects.select_related("topic", "topic__subject", "author")
            .order_by("topic__position", "order_in_topic", "-published_at", "title")
        )
        # Friendly filters by slugs
        subject_slug = self.request.query_params.get("subject") or self.kwargs.get("subject_slug")
        if subject_slug:
            qs = qs.filter(topic__subject__slug=subject_slug)

        topic_slug = self.request.query_params.get("topic") or self.kwargs.get("topic_slug")
        if topic_slug:
            qs = qs.filter(topic__slug=topic_slug)

        featured = self.request.query_params.get("featured")
        if featured in ("true", "1", "yes"):
            qs = qs.filter(is_featured=True)

        return qs

    def get_serializer_class(self):
        return ArticleDetailSerializer if self.action == "retrieve" else ArticleListSerializer