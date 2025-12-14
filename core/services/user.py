from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from core.models import User
from core.serializers.user import UserCreateSerializer
import requests

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
    def authenticate_user(email, password):
        user = authenticate(email=email, password=password)
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

    @staticmethod
    def info_edit(user, username=None, password=None):
        if username:
            user.username = username
        if password:
            user.set_password(password)
        user.save()
        return user


class AuthService:
    
    @staticmethod
    def get_naver_login_url():
        return (
            f"https://nid.naver.com/oauth2.0/authorize"
            f"?response_type=code"
            f"&client_id={settings.NAVER_CLIENT_ID}"
            f"&redirect_uri={settings.NAVER_REDIRECT_URI}"
            f"&state=some_random_state"
        )

    @staticmethod
    def handle_naver_callback(code, state):
        client_id = settings.NAVER_CLIENT_ID
        client_secret = settings.NAVER_CLIENT_SECRET
        redirect_uri = settings.NAVER_REDIRECT_URI

        token_request = requests.post(
            "https://nid.naver.com/oauth2.0/token",
            data={
                "grant_type": "authorization_code",
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "code": code,
                "state": state,
            },
        )

        token_json = token_request.json()
        access_token = token_json.get('access_token')
        profile_request = requests.get(
            "https://openapi.naver.com/v1/nid/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        profile_json = profile_request.json()
        response = profile_json.get("response")
        email = response.get("email")
        profile_image_url = response.get("profile_image")

        # 로그인 및 회원가입
        user = User.objects.filter(email=email).first()
        if user:
            return UserService.get_token(user)
        else:
            user = User.objects.create(email=email, profile_image=profile_image_url)
            return UserService.get_token(user)

