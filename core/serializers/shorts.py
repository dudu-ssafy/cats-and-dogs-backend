from core.models import Shorts
from rest_framework import serializers
from core.serializers.user import UserSimpleSerializer

class ShortsSerializer(serializers.ModelSerializer):
    author = UserSimpleSerializer(read_only=True)

    class Meta:
        model = Shorts
        fields = ['id', 'title', 'thumbnail_url', 'description', 'video_url', 'author']
