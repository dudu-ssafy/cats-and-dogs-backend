from rest_framework import serializers
from ..models.board import Board

class BoardSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username', read_only=True)
    date = serializers.SerializerMethodField()
    isLiked = serializers.SerializerMethodField()
    isNew = serializers.SerializerMethodField()
    likesCount = serializers.SerializerMethodField()

    authorProfileImg = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = [
            'id', 'category', 'title', 'content', 
            'author', 'authorProfileImg', 'views', 'date', 'isLiked', 'isNew', 'likesCount'
        ]
        read_only_fields = ['author', 'views', 'authorProfileImg']

    def get_authorProfileImg(self, obj):
        if obj.author and hasattr(obj.author, 'profile_img') and obj.author.profile_img:
            return obj.author.profile_img.url
        return None

    def get_likesCount(self, obj):
        return obj.like_users.count()

    def get_isLiked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_isNew(self, obj):
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
