from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.response import Response

# Create your views here.
from rest_framework.viewsets import ModelViewSet
from .models import Blog, Category
from .serializers import BlogSerializer, CategorySerializer, BlogListSerializer
from rest_framework.pagination import PageNumberPagination


class BlogPagination(PageNumberPagination):
    # Customize the page size for blogs specifically
    page_size_query_param = 'page_size'  # Allow clients to set page size


class BlogViewSet(ModelViewSet):
    """
    A viewset for managing blogs with custom filtering and actions.
    """
    queryset = Blog.objects.all().filter(status="published").order_by('-created_at')
    serializer_class = BlogSerializer
    pagination_class = BlogPagination

    def get_queryset(self):
        """
        Optionally filter blogs by status or category through query parameters.
        """
        queryset = super().get_queryset()
        status = self.request.query_params.get('status', None)  # Filter by status
        category = self.request.query_params.get('category', None)  # Filter by category ID
        search = self.request.query_params.get('search', None)  # Search by title or content

        if status:
            queryset = queryset.filter(status=status)
        if category:
            queryset = queryset.filter(categories__id=category)
        if search:
            queryset = queryset.filter(title__icontains=search) | queryset.filter(content__icontains=search)
        return queryset

    @action(detail=False, methods=['get'], url_path='slug/(?P<slug>[^/.]+)')
    def blog_by_slug(self, request, slug=None):
        """
        Custom action to retrieve a blog by its slug.
        """
        try:
            blog = Blog.objects.get(slug=slug)
        except Blog.DoesNotExist:
            return Response({"error": "Blog not found."}, status=404)

        serializer = self.get_serializer(blog)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='category/(?P<category_id>[^/.]+)')
    def blogs_by_category(self, request, category_id=None):
        """
        Custom action to retrieve blogs of a specific category.
        """
        blogs = Blog.objects.filter(categories__id=category_id).order_by('-created_at')
        page = self.paginate_queryset(blogs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(blogs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='featured')
    def featured_blogs(self, request):
        """
        Custom action to retrieve featured blogs.
        """
        featured_blogs = Blog.objects.filter(is_featured=True, status='published').order_by('-created_at')
        page = self.paginate_queryset(featured_blogs)

        serializer = BlogListSerializer(page or featured_blogs, many=True, context={"request": request})
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='recent')
    def recent_blogs(self, request):
        """
        Custom action to retrieve the most recent blogs.
        """
        recent_blogs = Blog.objects.all().order_by('-created_at')[:5]  # Limit to 5 recent blogs
        serializer = self.get_serializer(recent_blogs, many=True)
        return Response(serializer.data)


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
