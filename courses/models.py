from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField
from django.utils.text import slugify
from django.contrib.auth.models import User

from utils.validators import DynamicImageValidator


# Course Category Model
class CourseCategory(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# Course Model
class Course(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, null=True, max_length=191)
    thumbnail = models.ImageField(upload_to='courses/', blank=True, null=True, validators=[
        DynamicImageValidator(max_size_kb=500, max_width=1920, max_height=1080)])
    short_description = models.TextField(blank=True, null=True)
    description = RichTextUploadingField()
    price = models.IntegerField(default=0, help_text="price of the course")
    discounted_price = models.IntegerField(default=0)
    numbers_of_lessons = models.CharField(max_length=10, help_text="discounted price of the course")
    is_published = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)

    categories = models.ManyToManyField(CourseCategory, related_name='courses', blank=True)
    prerequisites = models.TextField(blank=True, null=True)
    level = models.CharField(
        max_length=20,
        choices=[('Beginner', 'Beginner'), ('Intermediate', 'Intermediate'), ('Advanced', 'Advanced')],
        default='Beginner'
    )
    total_duration = models.CharField(max_length=100, default="0", help_text="Total duration of the course.")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='courses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    watch_directly_from_yt = models.BooleanField(default=True)
    youtube_link = models.URLField(blank=True, null=True, default='https://www.youtube.com/@LearnCodeWithDurgesh')
    order = models.IntegerField(default=0)

    def discount_percentage(self):
        if self.price and self.price != 0:
            return int((self.discounted_price / self.price) * 100)
        return 0  # or None or '-' depending on what you'd like to show

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    # lesson course
    def lesson_counts(self):
        return self.lessons.count()

    def __str__(self):
        return self.title


# Lesson Model
class Lesson(models.Model):
    title = models.CharField(max_length=255)
    description = RichTextUploadingField()
    video = models.URLField(blank=True, null=True)
    order = models.PositiveIntegerField(help_text="Order in the course")
    is_preview = models.BooleanField(default=False, help_text="Mark as a free preview")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')

    def __str__(self):
        return self.title


# Attachment Model
class Attachment(models.Model):
    FILE_TYPES = [
        ('PDF', 'PDF'),
        ('ZIP', 'ZIP'),
        ('IMAGE', 'Image'),
        ('OTHER', 'Other')
    ]

    title = models.CharField(max_length=255, help_text="Title of the attachment", default='')
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='attachments/')
    file_type = models.CharField(max_length=20, choices=FILE_TYPES, default='OTHER')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')

    def __str__(self):
        return f"Attachment ({self.file_type})"
