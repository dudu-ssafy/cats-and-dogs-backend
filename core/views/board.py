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
        """
        게시글 목록을 조회합니다. 쿼리 파라미터로 필터링 가능합니다.

        사용 가능한 쿼리 파라미터:
        - category: 카테고리 ID 또는 이름
        - author: 작성자 ID 또는 username
        - search: 제목 또는 내용 검색
        - start_date: 시작 날짜 (YYYY-MM-DD)
        - end_date: 종료 날짜 (YYYY-MM-DD)

        예시: /boards/?category=1&search=강아지&start_date=2025-01-01
        """
        return BoardService.get_board_list(self.request.query_params)

    @action(detail=True, methods=['POST'], permission_classes = [IsAuthenticated], url_path='like')
    def like(self, request, pk=None):
        is_created = BoardService.toggle_like(request.user, pk)

        if is_created:
            return Response(status=status.HTTP_201_CREATED)
        
        return Response(status=status.HTTP_204_NO_CONTENT)
