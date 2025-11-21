from rest_framework import viewsets, status
from rest_framework.response import Response
from ..serializers.board import BoardSerializer
from ..models.board import Board

class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all().order_by('-created_at')
    serializer_class = BoardSerializer
    

