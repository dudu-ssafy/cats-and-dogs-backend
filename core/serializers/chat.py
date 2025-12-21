from rest_framework import serializers
from core.models.chat import ChatSession

class ChatSessionSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    profile_image = serializers.ImageField(source='user.profile_image', read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'username', 'profile_image', 'updated_at', 'last_message']

    def get_last_message(self, obj):
        if obj.history and isinstance(obj.history, list):
            last_msg = obj.history[-1]
            if isinstance(last_msg, dict):
                return last_msg.get('content', '')
        return ""

class ChatSessionDetailSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    profile_image = serializers.ImageField(source='user.profile_image', read_only=True)

    class Meta:
        model = ChatSession
        fields = '__all__'


class ChatSessionCreateSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'history', 'user']
