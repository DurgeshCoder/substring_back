# core/admin_base.py
from django.contrib import admin

class GlobalMediaAdmin(admin.ModelAdmin):
    class Media:
        js = ("admin/js/image_preview.js",)      # global JS
        css = {"all": ("admin/css/custom_admin.css",)}