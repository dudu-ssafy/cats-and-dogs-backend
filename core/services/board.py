from django.templatetags.static import static
from ..models.board import Board, BoardCategory
from ..models.like import BoardLike
from django.shortcuts import get_object_or_404
from django.db.models import F

class BoardService:

    @staticmethod
    def get_board_list(params: dict):
        queryset = Board.objects.all()

        category = params.get('category')
        if category:
            if category.isdigit():
                queryset = queryset.filter(category_id=category)
            else:
                queryset = queryset.filter(category__name__icontains=category)

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

        return queryset.order_by('-created_at')

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
    