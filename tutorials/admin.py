from django.contrib import admin
from .models import TutorialCategory, Subject, Topic
from unfold.admin import ModelAdmin


@admin.register(TutorialCategory)
class TutorialCategoryAdmin(ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Subject)
class SubjectAdmin(ModelAdmin):
    list_display = ('title', 'short_description', 'slug')
    search_fields = ('title', 'short_description', 'description')
    filter_horizontal = ('categories',)

    # Fix for slug issue
    readonly_fields = ('slug',)  # Mark 'slug' as readonly
    fieldsets = (
        (None, {
            'fields': ('title', 'categories', 'short_description', 'feature_image', 'description', 'slug')
        }),
    )


@admin.register(Topic)
class TopicAdmin(ModelAdmin):
    list_display = ('title', 'short_description', 'subject', 'slug', 'created_at', 'updated_at')
    search_fields = ('title', 'tags', 'subject__title', 'content', 'subject__title')
    readonly_fields = ('slug', 'created_at', 'updated_at',)
    list_filter = ('subject__title',)
    fieldsets = (
        (None, {
            'fields': ('title', 'subject', 'short_description', 'feature_image', 'content', 'tags', 'slug', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    class Media:
        js = ('js/ck_editor_init.js',)

