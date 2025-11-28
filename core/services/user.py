from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import User
from core.serializers.user import UserCreateSerializer


class UserService:
    @staticmethod
    def create_user(data):
        user = User.objects.create_user(**data)
        return user

    @staticmethod
    def get_token(user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    @staticmethod
    def authenticate_user(username, password):
        user = authenticate(username=username, password=password)
        if not user:
            raise AuthenticationFailed('로그인 정보가 일치하지 않습니다')
        return user

    @staticmethod
    def logout(refresh_token):
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception as e:
            raise AuthenticationFailed(e)
