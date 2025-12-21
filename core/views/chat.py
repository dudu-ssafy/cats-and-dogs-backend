from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from core.models.chat import ChatSession
from core.serializers.chat import ChatSessionSerializer, ChatSessionDetailSerializer, ChatSessionCreateSerializer
from core.services.chat import ChatService

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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            session, created = ChatService.upsert_chat_session(request.user, serializer.validated_data)
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response({'id': session.id}, status=status_code)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
