# admin.py
from django.contrib import admin
from django.utils.html import format_html

from .models import Subject, Topic, Article


# ---------- Inlines ----------
# class TopicInline(admin.TabularInline):
#     model = Topic
#     extra = 0
#     fields = ("name", "slug", "position", "is_active")
#     prepopulated_fields = {"slug": ("name",)}
#     show_change_link = True
#

# class ArticleInline(admin.TabularInline):
#     model = Article
#     extra = 0
#     fields = ("title", "slug", "status", "order_in_topic", "is_featured")
#     prepopulated_fields = {"slug": ("title",)}
#     show_change_link = True


# ---------- Subject ----------
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",

        "position",
        "updated_at",
        "default_difficulty",
        "is_active",
        "is_featured",
        "preview_visibility",

    )
    list_filter = ("visibility", "default_difficulty", "is_active", "is_featured")
    search_fields = ("name", "slug", "tagline", "description", "meta_title", "meta_description")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("position", "is_active", "is_featured")
    ordering = ("position", "name")
    readonly_fields = ("created_at", "updated_at")
    # inlines = [TopicInline]
    save_on_top = True
    list_per_page = 20

    fieldsets = (
        ("Basic", {
            "fields": (
                ("name", "slug"),
                "tagline",
                "description",
                ("icon", "cover_image"),
                ("visibility", "default_difficulty"),
                ("is_active", "is_featured", "position"),
                "owner",
            )
        }),
        ("SEO", {
            "classes": ("collapse",),
            "fields": (
                "meta_title",
                "meta_description",
                "meta_keywords",
                "canonical_url",
                ("og_title", "og_description", "og_image"),
            )
        }),
        ("Timestamps", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )

    @admin.display(description="visibility")
    def preview_visibility(self, obj):
        color = "green" if obj.visibility == "public" else "red"
        html = f'<span style="color:{color}">{obj.visibility.title()}</span>'
        return html

# ---------- Topic ----------
@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "subject",
        "is_active",
        "position",
        "created_at",
        "updated_at",

    )
    list_filter = ("is_active", "subject")
    search_fields = ("name", "slug", "summary", "meta_title", "meta_description", "subject__name")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("position", "is_active")
    ordering = ("subject__position", "position", "name")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("subject",)
    # inlines = [ArticleInline]
    save_on_top = True

    fieldsets = (
        ("Basic", {
            "fields": (
                "subject",
                ("name", "slug"),
                "summary",

                ("is_active", "position"),
            )
        }),

        ("Timestamps", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )



# ---------- Article ----------
@admin.action(description="Publish selected articles")
def mark_published(modeladmin, request, queryset):
    queryset.update(status="published")


@admin.action(description="Move selected to Draft")
def mark_draft(modeladmin, request, queryset):
    queryset.update(status="draft")


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "slug",
        "topic",
        "order_in_topic",
        "updated_at",
        "status",
        "is_featured",

    )
    list_filter = ("status", "difficulty", "is_featured", "topic", "topic__subject")
    search_fields = (
        "title",
        "slug",
        "excerpt",
        "content_html",
        "meta_title",
        "meta_description",
        "topic__name",
        "topic__subject__name",
    )
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("order_in_topic", "is_featured")
    ordering = ("topic__position", "order_in_topic", "-published_at", "title")
    readonly_fields = ("created_at", "updated_at", "computed_reading_minutes")
    autocomplete_fields = ("topic", "author")
    save_on_top = True
    actions = [mark_published, mark_draft]
    list_select_related = ("topic", "topic__subject", "author")

    fieldsets = (
        ("Placement", {
            "fields": ("topic", ("title", "slug"), ("status", "difficulty"), ("order_in_topic", "is_featured"))
        }),
        ("Content", {
            "fields": ("excerpt", "content_html", "cover_image")
        }),
        ("SEO", {
            "classes": ("collapse",),
            "fields": (
                "meta_title",
                "meta_description",
                "meta_keywords",
                "canonical_url",
                ("og_title", "og_description", "og_image"),
            )
        }),
        ("Publishing & Stats", {
            "classes": ("collapse",),
            "fields": (("published_at", "views", "likes"), ("created_at", "updated_at"), "computed_reading_minutes"),
        }),
        ("Authorship", {
            "classes": ("collapse",),
            "fields": ("author",),
        }),
    )

    @admin.display(description="Subject")
    def subject_name(self, obj):
        return obj.topic.subject.name

    @admin.display(description="Reading (min)")
    def computed_reading_minutes(self, obj):
        return obj.reading_minutes


    class Media:
        js = ('js/ck_editor_init.js',)