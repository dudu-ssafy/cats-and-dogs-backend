from ..models.board import Board, BoardCategory
from ..models.like import BoardLike
from django.shortcuts import get_object_or_404

class BoardService:

    #TODO hot, new에 대한 캐싱 query주기
    @staticmethod
    def get_board_list(
        category_name: str | None,
    ):
        queryset = Board.objects.all()
        if category_name:
            category = BoardCategory.objects.filter(name=category_name).first()
            queryset = queryset.filter(category=category)
        
        return queryset.order_by('-created_at')
    
    @staticmethod
    def toggle_like(user, board_id):
        board = get_object_or_404(Board, id=board_id)
        like, created = BoardLike.objects.get_or_create(user = user, board = board)
        
        if not created:
            like.delete()
            return False
        
        return True
    