from django.contrib.auth.models import User
from django.db import models


class Inquiry(models.Model):
    INQUIRY_TYPE_CHOICES = [
        ('business', 'Business'),
        ('student', 'Student'),
    ]

    type = models.CharField(max_length=20, choices=INQUIRY_TYPE_CHOICES)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    responded = models.BooleanField(default=False)
    responded_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.type})"
