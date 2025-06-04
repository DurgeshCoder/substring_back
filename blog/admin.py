from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Blog, Category, AuthorProfile
from unfold.admin import ModelAdmin


@admin.register(Blog)
class BlogAdmin(ModelAdmin):
    list_display = ('title', 'slug', 'meta_title', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('title',)}  # Auto-generate slug in admin
    search_fields = ('title', 'meta_title', 'meta_keywords')
    list_filter = ('created_at', 'updated_at')

    class Media:
        js = ('js/ck_editor.js',)


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(AuthorProfile)
class AuthorProfileAdmin(ModelAdmin):
    list_display = ('user',)
