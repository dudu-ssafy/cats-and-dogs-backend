from rest_framework import serializers
from ..models.board import Board

class BoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = [
            'title', 'content', 'author', 'created_at'
        ]
        read_only_fields = ['author']
