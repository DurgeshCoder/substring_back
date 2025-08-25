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
            "created_at", "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class SubjectDetailSerializer(SubjectListSerializer):
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

    subject_slug = serializers.CharField(source="subject.slug", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)

    class Meta:
        model = Topic
        fields = ("id", "name", "slug", "subject_slug", "subject_name", "position", "is_active")


class TopicListSerializer(serializers.ModelSerializer):
    subject = serializers.SlugRelatedField(slug_field="slug", queryset=Subject.objects.all())

    class Meta:
        model = Topic
        fields = (
            "id", "name", "slug", "summary",
            "is_active", "position",
            "subject",  # write/read by subject slug

            # computed
            "created_at", "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

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
        return ArticleListSerializer(qs, many=True, context=self.context).data


# ---------------------------
# Article
# ---------------------------
class ArticleListSerializer(serializers.ModelSerializer):
    topic_slug = serializers.CharField(source="topic.slug", read_only=True)
    subject_slug = serializers.CharField(source="topic.subject.slug", read_only=True)

    class Meta:
        model = Article
        fields = ("id", "title", "slug", "status", "order_in_topic", "published_at",
                  "topic_slug", "subject_slug",)


class ArticleDetailSerializer(SEOFieldsSerializerMixin, serializers.ModelSerializer):
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
            "created_at", "updated_at",
            "author",
        )
        read_only_fields = ("created_at", "updated_at", "views", "likes", "reading_minutes")

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


# Serializer for Getting subject--> topics--> articles
class TopicWithArticlesSerializer(serializers.ModelSerializer):
    articles = ArticleListSerializer(many=True, read_only=True)

    class Meta:
        model = Topic
        fields = ["id", "name", "slug","is_active", "articles"]


class SubjectWithTopicsSerializer(serializers.ModelSerializer):
    topics = TopicWithArticlesSerializer(many=True, read_only=True)

    class Meta:
        model = Subject
        fields = ['name', 'slug', 'topics', "id", "name", "slug", "tagline", "description",
                  "icon", "cover_image", "visibility", "default_difficulty",
                  "is_active", "is_featured", "position",
                  # SEO
                  "meta_title", "meta_description", "meta_keywords",
                  "canonical_url", "og_title", "og_description", "og_image",
                  # computed
                  "created_at", "updated_at", ]
