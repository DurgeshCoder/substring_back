from django.contrib import admin
from .models import CourseCategory, Course, Lesson, Attachment
from unfold.admin import ModelAdmin


@admin.register(CourseCategory)
class CourseCategoryAdmin(ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Course)
class CourseAdmin(ModelAdmin):
    list_display = ('title', 'author', 'price', 'is_published', 'is_premium', 'created_at', 'updated_at')
    list_filter = ('is_published', 'is_premium', 'categories', 'level', 'author')
    search_fields = ('title', 'short_description', 'description', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('categories',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title', 'thumbnail', 'slug', 'short_description', 'description', 'author', 'categories',
                'prerequisites', 'level',"numbers_of_lessons")
        }),
        ('Status', {
            'fields': ('is_published', 'is_premium')
        }),
        ('Additional Information', {
            'fields': (
                'price' ,"discount",'total_duration', 'created_at', 'updated_at', 'watch_directly_from_yt', 'youtube_link',
                'order')
        }),
    )

    class Media:
        js = ('js/ck_editor.js',)


@admin.register(Lesson)
class LessonAdmin(ModelAdmin):
    list_display = ('title', 'course', 'order', 'is_preview')
    list_filter = ('course', 'is_preview')
    search_fields = ('title', 'description', 'course__title')
    ordering = ('order',)
    fields = ('title', 'course', 'video', 'order', 'is_preview', 'description')

    class Media:
        js = ('js/ck_editor.js',)


@admin.register(Attachment)
class AttachmentAdmin(ModelAdmin):
    list_display = ('title', 'file', 'file_type', 'course', 'lesson', 'is_paid', 'price', 'uploaded_at')
    list_filter = ('file_type', 'course', 'lesson', 'course__title')
    search_fields = ('file', 'course__title', 'lesson__title')
    readonly_fields = ('uploaded_at',)
    fields = ('title', 'description', 'file', 'file_type', 'course', 'lesson', 'is_paid', 'price', 'uploaded_at')
