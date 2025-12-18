from core.models import Shorts
from rest_framework import viewsets, status
from rest_framework.response import Response
from core.services.shorts import ShortsService
from core.serializers.shorts import ShortsSerializer, ShortsDetailSerializer
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny

class ShortsViewSet(viewsets.ModelViewSet):
    queryset = Shorts.objects.all()
    serializer_class = ShortsSerializer

    def retrieve(self, request, pk=None):
        shorts = Shorts.objects.get(pk=pk)
        serializer = ShortsDetailSerializer(shorts)
        return Response(serializer.data)

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

    @action(detail=True, methods=['post'])
    def comment(self, request, pk):
        ShortsService.create_comment(request.user, pk, request.data['content'])
        return Response(status=status.HTTP_200_OK)