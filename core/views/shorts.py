from core.models import Shorts
from rest_framework import viewsets, status
from rest_framework.response import Response
from core.services.shorts import ShortsService
from core.serializers.shorts import ShortsSerializer
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny

class ShortsViewSet(viewsets.ModelViewSet):
    queryset = Shorts.objects.all()
    serializer_class = ShortsSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]

        return [IsAuthenticated()]

    def perform_create(self, serializer):
        shorts = serializer.save(author=self.request.user)
        ShortsService.create_shorts(shorts)

    @action(detail=True, methods=['post'])
    def like(self, request, pk):
        ShortsService.toggle_like(request.user, pk)
        return Response(status=status.HTTP_200_OK)
