from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.views import APIView

from substring_back.utils.email_helper import send_custom_email
from .models import Inquiry
from .serializers import InquirySerializer
from rest_framework.permissions import IsAuthenticated, AllowAny


class InquiryViewSet(viewsets.ModelViewSet):
    """
    A viewset for managing inquiries.
    """
    queryset = Inquiry.objects.all().order_by('-created_at')
    serializer_class = InquirySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['type', 'responded']
    search_fields = ['name', 'email', 'message']
    ordering_fields = ['created_at']
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access the API

    def perform_update(self, serializer):
        """
        Automatically set the responded_by field when marking as responded.
        """
        if serializer.validated_data.get('responded') is True:
            serializer.save(responded_by=self.request.user)
        else:
            serializer.save()

    @action(detail=False, methods=['get'])
    def unresponded(self, request):
        """
        Get all unresponded inquiries.
        """
        unresponded_inquiries = Inquiry.objects.filter(responded=False)
        serializer = self.get_serializer(unresponded_inquiries, many=True)
        return Response(serializer.data)


class EnquiryEmailAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        name = data.get('name')
        email = data.get('email')
        contact = data.get('contact')
        query = data.get('query')
        query_type = data.get('type')

        print(request.data)

        if not all([name, email, contact, query, query_type]):
            return Response({'error': 'All fields are required.'}, status=status.HTTP_400_BAD_REQUEST)

        subject = f"New {query_type.title()} Enquiry from {name}"
        body = f"""
        Name: {name}
        Email: {email}
        Contact: {contact}
        Type: {query_type}
        Query: {query}
        """

        try:
            send_custom_email(subject, body, to_emails=["learncodewithdurgesh@gmail.com"])
            return Response({'message': 'Enquiry email sent successfully.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
