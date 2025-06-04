from rest_framework import serializers
from .models import Inquiry


class InquirySerializer(serializers.ModelSerializer):
    responded_by_username = serializers.CharField(
        source='responded_by.username', read_only=True
    )  # Add responded_by username for readability

    class Meta:
        model = Inquiry
        fields = '__all__'
        read_only_fields = ['created_at', 'responded_by_username']
