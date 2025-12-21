from rest_framework import serializers
from ..models.board import Board

class BoardSerializer(serializers.ModelSerializer):
    categoryName = serializers.CharField(source='category.name', read_only=True)
    author = serializers.CharField(source='author.username', read_only=True)
    date = serializers.SerializerMethodField()
    isLiked = serializers.SerializerMethodField()
    isNew = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = [
            'id', 'category', 'categoryName', 'title', 'content', 
            'author', 'views', 'date', 'isLiked', 'isNew'
        ]
        read_only_fields = ['author', 'views']

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
