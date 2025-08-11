from django.contrib import admin

# Register your models here.
from django.contrib import admin

from utils.admin import GlobalMediaAdmin
from .models import Blog, Category, AuthorProfile

# Change admin site headers
admin.site.site_header = "Substring Technologies"
admin.site.site_title = "My Tutorial Website Portal"
admin.site.index_title = "Welcome to the Admin Dashboard"

@admin.register(Blog)
class BlogAdmin(GlobalMediaAdmin):
    list_display = ('title', 'slug', 'meta_title', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('title',)}  # Auto-generate slug in admin
    search_fields = ('title', 'meta_title', 'meta_keywords')
    list_filter = ('created_at', 'updated_at')

    class Media:
        js = ('js/ck_editor_init.js',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(AuthorProfile)
class AuthorProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)
