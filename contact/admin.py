from django.contrib import admin
from .models import Inquiry


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'type', 'responded', 'responded_by', 'created_at')
    list_filter = ('type', 'responded', 'created_at')
    search_fields = ('name', 'email', 'message', 'responded_by__username')
    readonly_fields = ('created_at',)
    fields = (
        'type',
        'name',
        'email',
        'phone_number',
        'message',
        'responded',
        'responded_by',
        'created_at',
    )
