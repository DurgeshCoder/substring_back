from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from utils.file_upload import AppendDateToFilename
from utils.mixins import FileCleanupMixin
from utils.validators import DynamicImageValidator, \
    SquareImageWithSizeValidator
import os


# author profile
class AuthorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    photo = models.ImageField(upload_to='author_photos/', blank=True, null=True,
                              validators=[SquareImageWithSizeValidator(max_size_kb=200)])
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def save(self, *args, **kwargs):
        """
        Handle:
        1. Delete the old photo if it exists and is being replaced.
        2. Save the new photo.
        """
        if self.pk:  # Check if the object already exists (not a new creation)
            try:
                old_instance = AuthorProfile.objects.get(pk=self.pk)
                # If the new photo is different from the old one, delete the old photo
                if old_instance.photo and old_instance.photo != self.photo:
                    if os.path.isfile(old_instance.photo.path):
                        os.remove(old_instance.photo.path)
            except AuthorProfile.DoesNotExist:
                pass  # If the object does not exist, skip deletion logic

        super().save(*args, **kwargs)  # Save the new instance

    def delete(self, *args, **kwargs):
        """
        Handle:
        1. Delete the associated photo file when the object is deleted.
        """
        if self.photo and os.path.isfile(self.photo.path):
            os.remove(self.photo.path)
        super().delete(*args, **kwargs)


# category
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


# blog

class Blog(FileCleanupMixin, models.Model):
    file_fields = ["featured_image"]  # used by FileCleanupMixin

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=191, unique=True, blank=True)
    short_content = models.TextField()
    content = RichTextUploadingField(config_name="blog")

    author = models.ForeignKey(
        AuthorProfile,
        on_delete=models.CASCADE,  # or models.PROTECT if you never want to lose posts
        related_name="blogs",
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft", db_index=True)
    categories = models.ManyToManyField(Category, blank=True, related_name="blogs")

    featured_image = models.ImageField(
        upload_to=AppendDateToFilename("blog_images", with_time=True),
        blank=True,
        null=True,
        validators=[DynamicImageValidator(max_size_kb=500, max_width=1920, max_height=1080)],
    )

    is_featured = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    published_at = models.DateTimeField(blank=True, null=True, db_index=True)

    # SEO
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "published_at"]),
            models.Index(fields=["is_featured", "published_at"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # slug (auto when blank)
        if not self.slug:
            self.slug = slugify(self.title)[:191]  # defensive trim

        # published_at management
        if self.status == "published" and not self.published_at:
            self.published_at = timezone.now()
        if self.status == "draft" and self.published_at:
            # if you prefer to keep original published_at, remove this block
            self.published_at = None

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog.detail", kwargs={"slug": self.slug})
