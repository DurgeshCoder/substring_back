# serializers.py
from __future__ import annotations
from django.utils.text import slugify
from django.db.models import Q
from rest_framework import serializers

from .models import Subject, Topic, Article


# ---------------------------
# Reusable SEO mixin
# ---------------------------
class SEOFieldsSerializerMixin(serializers.Serializer):
    meta_title = serializers.CharField(required=False, allow_blank=True, max_length=70)
    meta_description = serializers.CharField(required=False, allow_blank=True, max_length=160)
    meta_keywords = serializers.CharField(required=False, allow_blank=True, max_length=300)
    canonical_url = serializers.URLField(required=False, allow_blank=True)
    og_title = serializers.CharField(required=False, allow_blank=True, max_length=95)
    og_description = serializers.CharField(required=False, allow_blank=True, max_length=200)
    og_image = serializers.CharField(required=False, allow_blank=True, max_length=400)


# ---------------------------
# Subject
# ---------------------------
class SubjectListSerializer(SEOFieldsSerializerMixin, serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = (
            "id", "name", "slug", "tagline", "description",
            "icon", "cover_image", "visibility", "default_difficulty",
            "is_active", "is_featured", "position",
            # SEO
            "meta_title", "meta_description", "meta_keywords",
            "canonical_url", "og_title", "og_description", "og_image",
            # computed
            "url", "created_at", "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_url(self, obj) -> str:
        return obj.get_absolute_url()


class SubjectDetailSerializer(SubjectListSerializer):
    """Detail can additionally include a lightweight list of topics."""
    topics = serializers.SerializerMethodField()

    class Meta(SubjectListSerializer.Meta):
        fields = SubjectListSerializer.Meta.fields + ("topics",)

    def get_topics(self, obj):
        qs = getattr(obj, "topics", None).all() if hasattr(obj, "topics") else Topic.objects.filter(subject=obj)
        qs = qs.order_by("position", "name")
        return TopicMiniSerializer(qs, many=True, context=self.context).data


# ---------------------------
# Topic
# ---------------------------
class TopicMiniSerializer(serializers.ModelSerializer):
    """Used inside Subject detail or Article detail."""
    url = serializers.SerializerMethodField()
    subject_slug = serializers.CharField(source="subject.slug", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)

    class Meta:
        model = Topic
        fields = ("id", "name", "slug", "subject_slug", "subject_name", "position", "is_active", "url")

    def get_url(self, obj) -> str:
        return obj.get_absolute_url()


class TopicListSerializer(SEOFieldsSerializerMixin, serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    subject = serializers.SlugRelatedField(slug_field="slug", queryset=Subject.objects.all())

    class Meta:
        model = Topic
        fields = (
            "id", "name", "slug", "summary", "cover_image",
            "is_active", "position",
            "subject",  # write/read by subject slug
            # SEO
            "meta_title", "meta_description", "meta_keywords",
            "canonical_url", "og_title", "og_description", "og_image",
            # computed
            "url", "created_at", "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_url(self, obj) -> str:
        return obj.get_absolute_url()

    def validate(self, attrs):
        # Enforce unique (subject, slug) with nice error message
        name = attrs.get("name") or getattr(self.instance, "name", None)
        slug = attrs.get("slug") or (slugify(name) if name else None) or getattr(self.instance, "slug", None)
        subject = attrs.get("subject") or getattr(self.instance, "subject", None)

        if slug and subject:
            qs = Topic.objects.filter(subject=subject, slug=slug)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"slug": "Slug must be unique within this subject."})
        return attrs


class TopicDetailSerializer(TopicListSerializer):
    """Include lightweight article list under this topic."""
    articles = serializers.SerializerMethodField()

    class Meta(TopicListSerializer.Meta):
        fields = TopicListSerializer.Meta.fields + ("articles",)

    def get_articles(self, obj):
        qs = getattr(obj, "articles", None).all() if hasattr(obj, "articles") else Article.objects.filter(topic=obj)
        qs = qs.order_by("order_in_topic", "-published_at", "title")
        return ArticleMiniSerializer(qs, many=True, context=self.context).data


# ---------------------------
# Article
# ---------------------------
class ArticleMiniSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    topic_slug = serializers.CharField(source="topic.slug", read_only=True)
    subject_slug = serializers.CharField(source="topic.subject.slug", read_only=True)

    class Meta:
        model = Article
        fields = ("id", "title", "slug", "status", "order_in_topic", "published_at",
                  "topic_slug", "subject_slug", "url")

    def get_url(self, obj) -> str:
        return obj.get_absolute_url()


class ArticleListSerializer(SEOFieldsSerializerMixin, serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    topic = serializers.PrimaryKeyRelatedField(queryset=Topic.objects.all())  # safest for writes
    topic_slug = serializers.SlugRelatedField(source="topic", slug_field="slug",
                                              queryset=Topic.objects.all(), required=False, write_only=True)
    subject_slug = serializers.CharField(source="topic.subject.slug", read_only=True)
    reading_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Article
        fields = (
            "id", "title", "slug",
            "status", "difficulty",
            "topic",  # write by PK
            "topic_slug",  # optional write by topic slug (global uniqueness not guaranteed!)
            "subject_slug",  # read-only convenience
            "excerpt", "cover_image",
            "reading_minutes", "order_in_topic", "is_featured",
            "published_at", "views", "likes",
            "content_html",
            # SEO
            "meta_title", "meta_description", "meta_keywords",
            "canonical_url", "og_title", "og_description", "og_image",
            # computed
            "url", "created_at", "updated_at",
            "author",
        )
        read_only_fields = ("created_at", "updated_at", "views", "likes", "reading_minutes")

    def get_url(self, obj) -> str:
        return obj.get_absolute_url()

    def validate(self, attrs):
        # Unique (topic, slug) check with a friendly message
        title = attrs.get("title") or getattr(self.instance, "title", None)
        slug = attrs.get("slug") or (slugify(title) if title else None) or getattr(self.instance, "slug", None)
        topic = attrs.get("topic") or getattr(self.instance, "topic", None)

        if slug and topic:
            qs = Article.objects.filter(topic=topic, slug=slug)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"slug": "Slug must be unique within this topic."})
        return attrs


class ArticleDetailSerializer(ArticleListSerializer):
    """Detailed serializer for an article with related context."""
    topic_info = serializers.SerializerMethodField()
    subject_info = serializers.SerializerMethodField()
    related_articles = serializers.SerializerMethodField()
    author_info = serializers.SerializerMethodField()

    class Meta(ArticleListSerializer.Meta):
        fields = ArticleListSerializer.Meta.fields + (
            "topic_info",
            "subject_info",
            "related_articles",
            "author_info",
        )

    def get_topic_info(self, obj):
        topic = obj.topic
        return {
            "id": topic.id,
            "name": topic.name,
            "slug": topic.slug,
            "url": topic.get_absolute_url(),
        }

    def get_subject_info(self, obj):
        subject = obj.topic.subject
        return {
            "id": subject.id,
            "name": subject.name,
            "slug": subject.slug,
            "url": subject.get_absolute_url(),
        }

    def get_related_articles(self, obj):
        # Get other published articles from same topic
        qs = (
            Article.objects.filter(topic=obj.topic, status="published")
            .exclude(pk=obj.pk)
            .order_by("order_in_topic", "-published_at")[:5]
        )
        return ArticleMiniSerializer(qs, many=True, context=self.context).data

    def get_author_info(self, obj):
        if not obj.author:
            return None
        return {
            "id": obj.author.id,
            "username": getattr(obj.author, "username", ""),
            "full_name": getattr(obj.author, "get_full_name", lambda: "")(),
        }
