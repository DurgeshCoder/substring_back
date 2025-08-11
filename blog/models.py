from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

from utils.file_upload import append_date_to_filename
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
    file_fields = ['featured_image']

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, null=True, max_length=1000)
    short_content = models.TextField(blank=False, null=False)
    content = RichTextUploadingField(config_name="blog")
    author = models.ForeignKey(AuthorProfile, on_delete=models.CASCADE, related_name='blogs')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    categories = models.ManyToManyField(Category, blank=True, related_name='blogs')
    featured_image = models.ImageField(upload_to=append_date_to_filename("blog_images"), blank=True, null=True,
                                       validators=[
                                           DynamicImageValidator(max_size_kb=500, max_width=1920, max_height=1080)])
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)

    # SEO-related fields
    meta_title = models.CharField(max_length=255, blank=True, null=True)  # For <title> tag
    meta_description = models.TextField(blank=True, null=True)  # For <meta name="description">
    meta_keywords = models.TextField(blank=True, null=True)  # For <meta name="keywords">

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        Handle:
        1. Delete the old featured image if it exists and is being replaced.
        2. Save the new featured image.
        """
        if self.pk:  # Check if the object already exists
            try:
                old_instance = Blog.objects.get(pk=self.pk)
                # If the new image is different, delete the old image
                if old_instance.featured_image and old_instance.featured_image != self.featured_image:
                    if os.path.isfile(old_instance.featured_image.path):
                        os.remove(old_instance.featured_image.path)
            except Blog.DoesNotExist:
                pass  # If the object does not exist, skip deletion logic

        super().save(*args, **kwargs)  # Save the new instance

    def delete(self, *args, **kwargs):
        """
        Handle:
        1. Delete the associated featured image file when the object is deleted.
        """
        if self.featured_image and os.path.isfile(self.featured_image.path):
            os.remove(self.featured_image.path)
        super().delete(*args, **kwargs)
