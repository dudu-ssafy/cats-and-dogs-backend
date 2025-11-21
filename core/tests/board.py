from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models.board import BoardCategory, Board  # 모델이 core 앱에 있다고 가정

# settings.AUTH_USER_MODEL에 지정된 사용자 모델을 가져옵니다.
User = get_user_model()

class BoardModelTests(TestCase):
    """Board 및 BoardCategory 모델의 기본 CRUD 기능을 테스트합니다."""

    @classmethod
    def setUpTestData(cls):
        """테스트 클래스 전체에서 사용될 데이터를 한 번만 설정합니다."""
        
        # 1. 테스트 사용자 생성 (Board.author를 위한 준비)
        cls.user = User.objects.create_user(
            username='test_user',
            password='testpassword123',
            email='test@example.com'
        )

        # 2. 테스트 카테고리 생성 (Board.category를 위한 준비)
        cls.category_name = '자유게시판'
        cls.category = BoardCategory.objects.create(
            name=cls.category_name
        )

        # 3. 테스트 게시글 생성
        cls.board_title = '테스트 게시글 제목입니다.'
        cls.board_content = '여기에 내용이 들어갑니다.'
        cls.board = Board.objects.create(
            category=cls.category,
            title=cls.board_title,
            content=cls.board_content,
            author=cls.user
        )


    # ------------------------------------------------------------------
    # 1. 생성 (Create) 테스트
    # ------------------------------------------------------------------

    def test_category_creation(self):
        """BoardCategory 객체가 성공적으로 생성되고 필드가 올바른지 확인합니다."""
        category = self.category
        
        # 1-1. 객체 인스턴스 확인
        self.assertTrue(isinstance(category, BoardCategory))
        
        # 1-2. 필드 값 확인
        self.assertEqual(category.name, self.category_name)
        self.assertEqual(str(category), self.category_name) # __str__ 메서드 확인
        
    def test_board_creation(self):
        """Board 객체가 성공적으로 생성되고 필드 및 관계가 올바른지 확인합니다."""
        board = self.board
        
        # 2-1. 객체 인스턴스 확인
        self.assertTrue(isinstance(board, Board))
        
        # 2-2. 필드 값 확인
        self.assertEqual(board.title, self.board_title)
        self.assertEqual(board.content, self.board_content)
        self.assertEqual(str(board), self.board_title) # __str__ 메서드 확인
        self.assertIsNotNone(board.created_at) # 생성일자가 자동 설정되었는지 확인

    # ------------------------------------------------------------------
    # 2. 조회 (Get) 및 관계 테스트
    # ------------------------------------------------------------------

    def test_board_retrieval(self):
        """DB에서 게시글 객체가 성공적으로 조회되는지 확인합니다."""
        # PK(Primary Key)를 사용하여 객체를 조회합니다.
        board_from_db = Board.objects.get(pk=self.board.pk)
        
        # 조회된 객체의 값이 처음 생성된 객체의 값과 일치하는지 확인
        self.assertEqual(board_from_db.title, self.board_title)
        self.assertEqual(board_from_db.content, self.board_content)

    def test_foreign_key_relations(self):
        """Board 객체가 Category 및 Author와 올바르게 연결되었는지 확인합니다."""
        board = self.board
        
        # 1. Category 관계 확인 (Foreign Key)
        self.assertEqual(board.category, self.category)
        self.assertEqual(board.category.name, self.category_name)
        
        # 2. Author 관계 확인 (Foreign Key)
        self.assertEqual(board.author, self.user)
        self.assertEqual(board.author.username, 'test_user')

    def test_ordering(self):
        """Board 모델이 created_at을 기준으로 내림차순 정렬되는지 확인합니다."""
        
        # 두 번째 게시글 생성 (시간이 더 늦으므로 목록에서 맨 앞에 와야 합니다.)
        Board.objects.create(
            category=self.category,
            title='두 번째 게시글',
            content='나중에 작성됨',
            author=self.user
        )
        
        # 모든 게시글을 조회
        all_boards = Board.objects.all()
        
        # 생성일자 내림차순이므로 '두 번째 게시글'이 첫 번째로 와야 합니다.
        self.assertEqual(all_boards.first().title, '두 번째 게시글')
        self.assertEqual(all_boards.last().title, self.board_title)
