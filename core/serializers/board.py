from rest_framework import serializers
from ..models.board import Board

class BoardSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username', read_only=True)
    category_name = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_new = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    author_profile_img = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = [
            'id', 'category', 'category_name', 'title', 'content', 
            'author', 'author_profile_img', 'views', 'date', 'is_liked', 'is_new', 'likes_count', 'comment_count'
        ]
        read_only_fields = ['author', 'views', 'author_profile_img']

    def get_category_name(self, obj):
        mapping = {
            'free': '자유 수다',
            'qna': '질문/답변',
            'info': '정보 공유'
        }
        return mapping.get(obj.category, obj.category)

    def get_author_profile_img(self, obj):
        if obj.author and hasattr(obj.author, 'profile_image') and obj.author.profile_image:
            return obj.author.profile_image
        return None

    def get_likes_count(self, obj):
        return obj.like_users.count()

    def get_comment_count(self, obj):
        # BoardComment 모델이 아직 정의되지 않았을 수 있으므로 0 반환 또는 관련 필드 확인
        return 0 

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_is_new(self, obj):
        from django.utils import timezone
        import datetime
        return obj.created_at >= timezone.now() - datetime.timedelta(days=1)

    def get_date(self, obj):
        from django.utils import timezone
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days == 0:
            return obj.created_at.strftime('%H:%M')
        return obj.created_at.strftime('%Y-%m-%d')
