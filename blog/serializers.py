from rest_framework import serializers
from .models import Blog, Category, AuthorProfile


class BlogSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.user',
                                        read_only=True)  # Use the username field of the related author
    author = serializers.PrimaryKeyRelatedField(queryset=AuthorProfile.objects.all(), )

    class Meta:
        model = Blog
        fields = [
            'id', 'title', 'slug', 'author_name', 'content', 'featured_image',
            'author', 'status', 'categories', 'created_at', 'updated_at', 'published_at', "short_content",
            "meta_title","meta_description","meta_keywords"
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if self.context.get('view').action == 'list':
            representation.pop('content', None)
            representation.pop('categories', None)
        return representation


# Blog Serializer without content and categories

# serializers.py
from rest_framework import serializers
from .models import Blog


class BlogListSerializer(serializers.ModelSerializer):
    featured_image = serializers.ImageField(use_url=True)
    author = serializers.CharField(source='author.user')  # Use the username field of the related author

    class Meta:
        model = Blog
        # Exclude 'content' field for list or featured view
        exclude = ['content', "categories", 'meta_title', 'meta_description', 'meta_keywords', ]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']
        read_only_fields = ['id']


class AuthorProfileSerializer(serializers.ModelSerializer):
    username=serializers.ReadOnlyField(source='user.first_name')
    class Meta:
        model = AuthorProfile
        fields = ['id', 'user', 'bio','username']