from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.utils.html import format_html

from utils.admin import GlobalMediaAdmin
from .models import Blog, Category, AuthorProfile

# Change admin site headers
admin.site.site_header = "Substring Technologies"
admin.site.site_title = "My Tutorial Website Portal"
admin.site.index_title = "Welcome to the Admin Dashboard"


@admin.register(Blog)
class BlogAdmin(GlobalMediaAdmin):
    list_display = ('title', 'meta_title', 'created_at', 'color_status')
    prepopulated_fields = {'slug': ('title',)}  # Auto-generate slug in admin
    autocomplete_fields = ('categories','author')
    search_fields = ('title', 'meta_title', 'meta_keywords',)
    list_filter = ('status','created_at', 'updated_at')
    ordering = ['-created_at']


    list_per_page = 15
    def color_status(self, obj):
        if obj.status == "published":
            color = "green"
        else:
            color = "red"
        return format_html(f'<span style="color:{color}">{obj.status}</span>')

    class Media:
        js = ('js/ck_editor_init.js',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(AuthorProfile)
class AuthorProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
