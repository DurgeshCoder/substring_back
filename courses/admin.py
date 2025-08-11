from django.contrib import admin

from utils.admin import GlobalMediaAdmin
from .models import CourseCategory, Course, Lesson, Attachment

@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Course)
class CourseAdmin(GlobalMediaAdmin):
    list_display = ('title', 'author', 'price', 'is_published', 'is_premium', 'created_at', 'updated_at',
                    'discount_percentage_display')
    list_filter = ('is_published', 'is_premium', 'categories', 'level', 'author')
    search_fields = ('title', 'short_description', 'description', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('categories',)
    readonly_fields = ('created_at', 'updated_at', 'discount_percentage_display')
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title', 'thumbnail', 'slug', 'short_description', 'description', 'author', 'categories',
                'prerequisites', 'level', "numbers_of_lessons")
        }),
        ('Status', {
            'fields': ('is_published', 'is_premium')
        }),
        ('Additional Information', {
            'fields': (
                'price', "discounted_price", "discount_percentage_display", 'total_duration', 'created_at',
                'updated_at',
                'watch_directly_from_yt', 'youtube_link',
                'order')
        }),
    )

    def discount_percentage_display(self, obj):
        return obj.discount_percentage()

    discount_percentage_display.short_description = 'Discount %'

    class Media:
        js = ('js/ck_editor_init.js',)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'is_preview')
    list_filter = ('course', 'is_preview')
    search_fields = ('title', 'description', 'course__title')
    ordering = ('order',)
    fields = ('title', 'course', 'video', 'order', 'is_preview', 'description')

    class Media:
        js = ('js/ck_editor_init.js',)


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'file', 'file_type', 'course', 'lesson', 'is_paid', 'price', 'uploaded_at')
    list_filter = ('file_type', 'course', 'lesson', 'course__title')
    search_fields = ('file', 'course__title', 'lesson__title')
    readonly_fields = ('uploaded_at',)
    fields = ('title', 'description', 'file', 'file_type', 'course', 'lesson', 'is_paid', 'price', 'uploaded_at')
