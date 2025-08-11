from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Testimonial


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('author_name', 'author_designation', 'is_featured', 'created_at')
    list_filter = ('is_featured',)
    search_fields = ('author_name', 'author_designation', 'content', 'linkedin_url', 'twitter_url', 'website_url')
    readonly_fields = ('created_at',)
    fields = (
        'author_name',
        'author_designation',
        'content',
        'image',
        'is_featured',
        'linkedin_url',
        'twitter_url',
        'website_url',
        'created_at'
    )
