from rest_framework import viewsets, status
from rest_framework.response import Response
from core.serializers.board import BoardSerializer
from core.models.board import Board
from core.services.board import BoardService

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from core.services.redis import RedisService
from rest_framework.pagination import PageNumberPagination

class BoardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    pagination_class = BoardPagination

    def get_queryset(self):
        """
        게시글 목록을 조회합니다. 쿼리 파라미터로 필터링 가능합니다.
        """
        return BoardService.get_board_list(
            self.request.query_params,
            self.request.user
        )

    def retrieve(self, request, *args, **kwargs):
        board = self.get_object()
        BoardService.update_views(board.id)
        # Redis에 조회수 및 사용자 최근 본 글 기록
        RedisService.record_view(request.user.id if request.user.is_authenticated else None, board.id)

        serializer = self.get_serializer(board)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'], permission_classes = [IsAuthenticated], url_path='like')
    def like(self, request, pk=None):
        is_created = BoardService.toggle_like(request.user, pk)

        if is_created:
            return Response(status=status.HTTP_201_CREATED)
        
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['GET'], permission_classes = [IsAuthenticated], url_path='me')
    def me(self, request):
        """
        현재 사용자가 작성한 게시글 목록을 반환합니다.
        """
        boards = Board.objects.filter(author=request.user)
        serializer = self.get_serializer(boards, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'], permission_classes = [IsAuthenticated], url_path='likes')
    def likes(self, request):
        """
        현재 사용자가 좋아요한 게시글 목록을 반환합니다.
        """
        boards = Board.objects.filter(likes__user=request.user)
        serializer = self.get_serializer(boards, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'], permission_classes = [IsAuthenticated], url_path='recent')
    def recent(self, request):
        """
        현재 사용자가 최근에 본 게시글 목록을 반환합니다. (최대 20개)
        """
        board_ids = RedisService.get_user_recent_board_ids(request.user.id)
        
        if not board_ids:
            return Response([])

        # Redis 순서(최신순)를 유지하며 DB 조회
        # PostgreSQL의 경우 Case When 또는 id__in + python sorting 방식 사용
        boards = Board.objects.filter(id__in=board_ids)
        board_dict = {str(b.id): b for b in boards}
        ordered_boards = [board_dict[bid] for bid in board_ids if bid in board_dict]

        serializer = self.get_serializer(ordered_boards, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'], url_path='popular')
    def popular(self, request):
        """
        집계된 인기 게시글 목록을 반환합니다.
        """
        board_ids = RedisService.get_cached_popular_board_ids()
        
        if not board_ids:
            # 캐시가 없을 경우 전체 조회수 순 폴백
            boards = Board.objects.all().order_by('-views', '-created_at')[:10]
        else:
            boards = Board.objects.filter(id__in=board_ids)
            board_dict = {str(b.id): b for b in boards}
            ordered_boards = [
                board_dict[bid] for bid in board_ids 
                if bid in board_dict
            ]
            boards = ordered_boards

        serializer = self.get_serializer(boards, many=True)
        return Response(serializer.data)
