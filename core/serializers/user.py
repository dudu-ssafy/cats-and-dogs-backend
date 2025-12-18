from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from core.models import User

class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'profile_image']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    email = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'profile_image',
        ]

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'profile_image',
            'last_login',
            'date_joined',
        ]
