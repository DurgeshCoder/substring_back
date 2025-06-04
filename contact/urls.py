from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InquiryViewSet, EnquiryEmailAPIView

router = DefaultRouter()
router.register(r'inquiries', InquiryViewSet, basename='inquiry')

urlpatterns = [
    path('', include(router.urls)),
    path('enquiry/email/', EnquiryEmailAPIView.as_view(), name='enquiry-email'),
]
