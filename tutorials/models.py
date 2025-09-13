from __future__ import annotations
import re

from ckeditor_uploader.fields import RichTextUploadingField
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, URLValidator
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse

from utils.file_upload import AppendDateToFilename
from utils.mixins import FileCleanupMixin
from utils.validators import DynamicImageValidator


# ---------------------------
# Common mixins / base models
# ---------------------------
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


class SEOFields(models.Model):
    meta_title = models.CharField(max_length=70, blank=True, help_text="Recommended ≤ 60–70 chars")
    meta_description = models.CharField(max_length=160, blank=True, help_text="Recommended ≤ 150–160 chars")
    meta_keywords = models.CharField(max_length=300, blank=True, help_text="Comma-separated (optional)")
    canonical_url = models.URLField(blank=True)
    og_title = models.CharField(max_length=95, blank=True)
    og_description = models.CharField(max_length=200, blank=True)
    og_image = models.CharField(max_length=400, blank=True, help_text="URL or media key")

    class Meta:
        abstract = True


# -------------
# Core entities
# -------------
class Subject(FileCleanupMixin, SEOFields, TimeStampedModel):
    file_fields = ['cover_image']
    """
    Top-level learning area (e.g., Java, Python)
    """
    VISIBILITY = (("public", "Public"), ("private", "Private"))
    DIFFICULTY = (("beginner", "Beginner"), ("intermediate", "Intermediate"), ("advanced", "Advanced"))

    name = models.CharField(max_length=160, unique=True)
    slug = models.SlugField(max_length=180, unique=True, help_text="Used in URL, auto-filled from name")
    tagline = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=120, blank=True, help_text="Icon class or emoji")
    cover_image = models.ImageField(upload_to=AppendDateToFilename("tutorials/subjects/cover_images", with_time=True),
                                    blank=True,
                                    validators=[
                                        DynamicImageValidator(max_size_kb=500, max_width=1920, max_height=1080)],
                                    help_text="Cover image for subjects page")
    visibility = models.CharField(max_length=10, choices=VISIBILITY, default="public", db_index=True)
    default_difficulty = models.CharField(max_length=12, choices=DIFFICULTY, default="beginner")
    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    position = models.PositiveIntegerField(default=0, help_text="Order on subjects page", db_index=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="subjects"
    )

    class Meta:
        ordering = ["position", "name"]
        indexes = [
            models.Index(fields=["is_active", "position"]),
            models.Index(fields=["visibility", "position"]),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    # Topic model


class Topic(TimeStampedModel):
    """
    Section within a subject (e.g., Core Basics, OOPs)
    """
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="topics")
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, help_text="Unique within subject")
    summary = models.TextField(blank=True)
    # cover_image = models.CharField(max_length=400, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    position = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        unique_together = (("subject", "slug"),)  # keeps URLs clean within a subject
        ordering = ["subject__position", "position", "name"]
        indexes = [
            models.Index(fields=["subject", "position"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.subject.name} → {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Article(SEOFields, TimeStampedModel):
    file_fields = ['cover_image']
    """
    A lesson/page inside a Topic.
    """
    STATUS = (
        ("draft", "Draft"),
        ("review", "In Review"),
        ("published", "Published"),
        ("archived", "Archived"),
    )
    DIFFICULTY = (("beginner", "Beginner"), ("intermediate", "Intermediate"), ("advanced", "Advanced"))

    topic = models.ForeignKey(Topic, on_delete=models.PROTECT, related_name="articles")
    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, help_text="Unique within topic")
    status = models.CharField(max_length=10, choices=STATUS, default="draft", db_index=True)
    difficulty = models.CharField(max_length=12, choices=DIFFICULTY, default="beginner", db_index=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="articles"
    )

    # Content — choose one of the following depending on your editor:
    # If using CKEditor/Quill and storing HTML:
    content_html = RichTextUploadingField(help_text="Rendered HTML content", config_name="tutorials")

    # Optional extras:
    excerpt = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to=AppendDateToFilename("tutorials/articles/cover_images", with_time=True),
                                    validators=[
                                        DynamicImageValidator(max_size_kb=500, max_width=1920, max_height=1080)],
                                    help_text="Cover image for articles page")
    reading_minutes = models.PositiveIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(120)],
        help_text="Estimated reading time (minutes)"
    )
    order_in_topic = models.PositiveIntegerField(default=0, db_index=True, help_text="Sidebar order")
    is_featured = models.BooleanField(default=False, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)

    # Engagement counters (denormalized, optional)
    views = models.PositiveIntegerField(default=0, db_index=True)
    likes = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = (("topic", "slug"),)
        ordering = ["topic__position", "order_in_topic", "-published_at", "title"]
        indexes = [
            models.Index(fields=["status", "published_at"]),
            models.Index(fields=["topic", "order_in_topic"]),
            models.Index(fields=["difficulty"]),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        # Auto-fill reading time if empty (simple heuristic ~200 wpm)
        if not self.reading_minutes and self.content_html:
            text = re.sub(r"<[^>]+>", " ", self.content_html or "")
            words = len([w for w in text.split() if w.strip()])
            self.reading_minutes = max(1, round(words / 200))
        super().save(*args, **kwargs)
