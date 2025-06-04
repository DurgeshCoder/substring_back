from rest_framework import serializers
from .models import TutorialCategory, Subject, Topic


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = '__all__'
        read_only_fields = ['slug', 'created_at', 'updated_at']


class SubjectSerializer(serializers.ModelSerializer):
    topics = TopicSerializer(many=True, read_only=True)
    categories = serializers.PrimaryKeyRelatedField(many=True, queryset=TutorialCategory.objects.all())

    class Meta:
        model = Subject
        fields = '__all__'
        read_only_fields = ['slug']


class TutorialCategorySerializer(serializers.ModelSerializer):
    subjects = SubjectSerializer(many=True, read_only=True)

    class Meta:
        model = TutorialCategory
        fields = '__all__'
        read_only_fields = ['slug']
