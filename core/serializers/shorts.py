from core.models.shorts import Shorts, ShortsComment
from rest_framework import serializers
from core.serializers.user import UserSimpleSerializer

class ShortsSerializer(serializers.ModelSerializer):
    author = UserSimpleSerializer(read_only=True)

    class Meta:
        model = Shorts
        fields = ['id', 'title', 'thumbnail_url', 'description', 'video_url', 'author']

class ShortsDetailSerializer(serializers.ModelSerializer):
    author = UserSimpleSerializer(read_only=True)
    comments = serializers.SerializerMethodField()

    class Meta:
        model = Shorts
        fields = ['id', 'title', 'thumbnail_url', 'description', 'video_url', 'author', 'comments']

    def get_comments(self, obj):
        return ShortsCommentSerializer(obj.comments.all(), many=True).data


class ShortsCommentSerializer(serializers.ModelSerializer):
    author = UserSimpleSerializer(read_only=True)

    class Meta:
        model = ShortsComment
        fields = ['id', 'content', 'author', 'created_at']
