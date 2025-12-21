from django.templatetags.static import static
from ..models.board import Board
from ..models.like import BoardLike
from django.shortcuts import get_object_or_404
from django.db.models import F

class BoardService:

    @staticmethod
    def get_board_list(params: dict, user=None):
        queryset = Board.objects.all()

        filter_type = params.get('type')
        
        if filter_type == 'hot':
            from core.services.redis import RedisService
            board_ids = RedisService.get_cached_popular_board_ids()
            if not board_ids:
                # 캐시가 없을 경우 조회수가 100 이상인 글을 최신순으로 반환하거나 
                # 단순히 조회수 높은 순으로 폴백
                queryset = queryset.filter(views__gte=100).order_by('-views', '-created_at')
            else:
                # Redis의 ID 순서 유지 (PostgreSQL Field-like sorting)
                from django.db.models import Case, When
                preserved = Case(*[When(id=pk, then=pos) for pos, pk in enumerate(board_ids)])
                queryset = queryset.filter(id__in=board_ids).order_by(preserved)
        elif filter_type == 'my-posts' and user and user.is_authenticated:
            queryset = queryset.filter(author=user)
        elif filter_type == 'liked-posts' and user and user.is_authenticated:
            queryset = queryset.filter(likes__user=user)
        else:
            # 일반 카테고리 필터링
            category = params.get('category')
            if category:
                if category.isdigit():
                    queryset = queryset.filter(category_id=category)
                else:
                    queryset = queryset.filter(category=category)

        author = params.get('author')
        if author:
            if author.isdigit():
                queryset = queryset.filter(author_id=author)
            else:
                queryset = queryset.filter(author__username__icontains=author)

        search = params.get('search')
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )

        start_date = params.get('start_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)

        end_date = params.get('end_date')
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        if filter_type != 'hot':
            queryset = queryset.order_by('-created_at')
            
        return queryset

    @staticmethod
    def update_views(board_id):
        # F객체를 씀으로 데이터 유실 없이 진행
        Board.objects.filter(id=board_id).update(views=F('views') + 1)

    @staticmethod
    def toggle_like(user, board_id):
        board = get_object_or_404(Board, id=board_id)
        like, created = BoardLike.objects.get_or_create(user = user, board = board)
        
        if not created:
            like.delete()
            return False
        
        return True
    