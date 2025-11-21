from ..models.board import Board, BoardCategory

class BoardService:

    #TODO hot, new에 대한 캐싱 query주기
    @staticmethod
    def get_board_list(
        category_name: str | None,
    ):
        queryset = Board.objects.all()
        if category_name:
            category = BoardCategory.objects.get(name=category_name)
            queryset = queryset.filter(category=category)
        
        return queryset
