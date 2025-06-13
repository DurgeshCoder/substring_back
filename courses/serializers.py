from rest_framework import serializers
from .models import CourseCategory, Course, Lesson, Attachment


# Attachment Serializer
class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'
        read_only_fields = ['uploaded_at']


# Lesson Serializer
class LessonSerializer(serializers.ModelSerializer):
    attachments = AttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = '__all__'
        read_only_fields = ['id']


# Course Serializer
class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    # author = serializers.CharField(source='author.username', read_only=True)
    author = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ['id', 'slug', 'total_duration', 'created_at', 'updated_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Exclude lessons and attachments for list view
        if self.context.get('view') is not None and self.context.get('view').action == 'list':
            representation.pop('lessons', None)
            representation.pop('attachments', None)
            representation.pop('description', None)
        return representation

    def get_author(self, obj):
        return f"{obj.author.first_name} {obj.author.last_name}".strip()

    def get_discount_percentage(self, obj):
        return obj.discount_percentage()

    def get_thumbnail(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None


# Course Category Serializer
class CourseCategorySerializer(serializers.ModelSerializer):
    courses = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    # courses = CourseSerializer(many=True, read_only=True)

    class Meta:
        model = CourseCategory
        fields = '__all__'


# for specific api


class CourseSerializer1(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ['id', 'slug', 'total_duration', 'created_at', 'updated_at']


class CourseCategorySerializer1(serializers.ModelSerializer):
    # courses = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    courses = CourseSerializer1(many=True, read_only=True)

    class Meta:
        model = CourseCategory
        fields = '__all__'
