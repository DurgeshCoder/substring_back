from django.db.models import Q
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
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

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    # search across fields
    search_fields = ["title", "content"]  # ?search=react
    # allow clients to order
    ordering_fields = ["created_at", "title"]
    ordering = ["-created_at"]  # default

    # exact-match filters
    filterset_fields = {
        "status": ["exact"],  # ?status=published|draft
        "is_featured": ["exact"],  # ?is_featured=true
        "categories": ["exact"],  # ?categories=<id>
    }

    def get_queryset(self):
        """
        Optionally filter blogs by status or category through query parameters.
        """
        qs = (
            Blog.objects
            .all()
            .select_related("author")  # if you have author FK
            .prefetch_related("categories")  # if ManyToMany
        )

        # default to published unless user asks otherwise
        status_param = self.request.query_params.get("status")
        if not status_param:
            qs = qs.filter(status="published")

        # optional extra OR search field (if you want custom logic)
        # DRF's SearchFilter already covers ?search=...,
        # but here’s how to layer custom behavior if needed:
        s = self.request.query_params.get("search_extra")
        if s:
            qs = qs.filter(Q(title__icontains=s) | Q(content__icontains=s))

        # avoid dupes when filtering through M2M
        return qs.distinct()

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
        blogs = Blog.objects.filter(categories__id=category_id).filter(status='published').order_by('-created_at')
        page = self.paginate_queryset(blogs)
        if page is not None:
            serializer = BlogListSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(blogs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='featured')
    def featured_blogs(self, request):
        """
        Custom action to retrieve featured blogs.
        """
        featured_blogs = Blog.objects.filter(is_featured=True, status='published').order_by('-created_at')[0:6]
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

    def get_serializer_class(self):
        # compact list payload vs rich detail
        if self.action == "list":
            return BlogListSerializer
        return BlogSerializer


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
