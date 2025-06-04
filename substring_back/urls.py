"""
URL configuration for substring_back project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls.py import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls.py'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.urls.conf import include, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view

from rest_framework.permissions import AllowAny

from substring_back import settings
from substring_back.views import delete_image
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


schema_view = get_schema_view(
    openapi.Info(
        title="Substring Back API",
        default_version='v1',
        description="API documentation for all endpoints",
        terms_of_service="https://substringtechnologies.com",
        contact=openapi.Contact(email="support@substringtechnologies.com"),
    ),
    public=True,
    permission_classes=[AllowAny, ],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('blog.urls')),
    path('api/v1/', include('courses.urls')),
    path('api/v1/', include('tutorials.urls')),
    path('api/v1/', include('testimonials.urls')),
    path('api/v1/', include('contact.urls')),
    path('api/v1/generate-token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/refresh-token', TokenRefreshView.as_view(), name='token_refresh'),

    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('ckeditor/', include('ckeditor_uploader.urls')),  # CKEditor file upload URLs
    path('ckeditor/delete/', delete_image, name='ckeditor_delete_image'),

]
# Add media files URL configuration
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
