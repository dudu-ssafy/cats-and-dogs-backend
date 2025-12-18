from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from core.models.chat import ChatSession
from core.serializers.chat import ChatSessionSerializer, ChatSessionDetailSerializer, ChatSessionCreateSerializer

class ChatSessionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return ChatSessionSerializer
        elif self.action == 'retrieve':
            return ChatSessionDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ChatSessionCreateSerializer
        return ChatSessionSerializer

    def create(self, *args, **kwargs):
        serializer = self.get_serializer(data=self.request.data)
        if serializer.is_valid():
            serializer.save(user=self.request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
