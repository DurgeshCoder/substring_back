from django.db import models

# Create your models here.
from django.db import models
from utils.validators import SquareImageWithSizeValidator


class Testimonial(models.Model):
    author_name = models.CharField(max_length=255)
    author_designation = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField()
    image = models.ImageField(upload_to='testimonials/images/', blank=True, null=True, validators=[
        SquareImageWithSizeValidator(max_size_kb=200)
    ])
    is_featured = models.BooleanField(default=False, help_text="Mark as featured testimonial")
    linkedin_url = models.URLField(blank=True, null=True, help_text="LinkedIn profile link")
    twitter_url = models.URLField(blank=True, null=True, help_text="Twitter profile link")
    website_url = models.URLField(blank=True, null=True, help_text="Personal or professional website")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author_name} - {self.author_designation or 'Anonymous'}"
