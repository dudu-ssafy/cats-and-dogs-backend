from rest_framework import viewsets, status
from rest_framework.response import Response
from ..serializers.board import BoardSerializer
from ..models.board import Board
from ..services.board import BoardService

class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer

    def get_queryset(self):
        category_param = self.request.query_params.get('category')
        return BoardService.get_board_list(category_param)
