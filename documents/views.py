from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Document
from .serializers import DocumentSerializer


class DocumentUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DocumentSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)


class DocumentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        docs = Document.objects.filter(user=request.user)
        serializer = DocumentSerializer(docs, many=True)
        return Response(serializer.data)


class DocumentDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            doc = Document.objects.get(pk=pk, user=request.user)
            doc.delete()
            return Response(status=204)
        except Document.DoesNotExist:
            return Response(status=404)