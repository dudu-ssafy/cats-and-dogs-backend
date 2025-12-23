from core.models.shorts import Shorts, ShortsComment
from core.models.like import ShortsLike
from rest_framework import serializers
from core.serializers.user import UserSimpleSerializer

class ShortsSerializer(serializers.ModelSerializer):
    author = UserSimpleSerializer(read_only=True)
    likes_count = serializers.IntegerField(source='likes.count', read_only=True)
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Shorts
        fields = ['id', 'title', 'thumbnail_url', 'video_url', 'author', 'likes_count', 'comments_count', 'is_liked']

    def get_is_liked(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return obj.likes.filter(user=user).exists()
        return False

class ShortsSimpleSerializer(serializers.ModelSerializer):
    likes_count = serializers.IntegerField(source='likes.count', read_only=True)

    class Meta:
        model = Shorts
        fields = ['id', 'title', 'thumbnail_url', 'likes_count']

class ShortsDetailSerializer(serializers.ModelSerializer):
    author = UserSimpleSerializer(read_only=True)
    comments = serializers.SerializerMethodField()

    class Meta:
        model = Shorts
        fields = ['id', 'title', 'thumbnail_url', 'video_url', 'author', 'comments']

    def get_comments(self, obj):
        return ShortsCommentSerializer(obj.comments.all(), many=True).data


class ShortsCommentSerializer(serializers.ModelSerializer):
    author = UserSimpleSerializer(read_only=True)

    class Meta:
        model = ShortsComment
        fields = ['id', 'content', 'author', 'created_at']
