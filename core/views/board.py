from rest_framework import viewsets, status
from rest_framework.response import Response
from ..serializers.board import BoardSerializer
from ..models.board import Board
from ..services.board import BoardService

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer

    def get_queryset(self):
        category_param = self.request.query_params.get('category')
        return BoardService.get_board_list(category_param)
    
    @action(detail=True, methods=['POST'], permission_classes = [IsAuthenticated], url_path='like')
    def like(self, request, pk=None):
        is_created = BoardService.toggle_like(request.user, pk)
        
        if is_created:
            return Response(status=status.HTTP_201_CREATED)
        
        return Response(status=status.HTTP_204_NO_CONTENT)