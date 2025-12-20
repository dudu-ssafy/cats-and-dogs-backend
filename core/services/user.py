from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from core.models import User
from core.serializers.user import UserCreateSerializer
import requests
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from urllib.parse import urlencode

class EmailBackend(ModelBackend):
    """
    이메일과 비밀번호로 인증하도록 오버라이드합니다.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None

        if user.check_password(password):
            return user
        return None

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

        user = User.objects.filter(email=email).first()
        if user:
            return UserService.get_token(user)
        else:
            user = User.objects.create(email=email, profile_image=profile_image_url)
            return UserService.get_token(user)

    @staticmethod
    def get_google_login_url():
        GOOGLE_SCOPE_USERINFO = "https://www.googleapis.com/auth/userinfo.email"
        GOOGLE_SCOPE_PROFILE = "https://www.googleapis.com/auth/userinfo.profile"
        scope = f'{GOOGLE_SCOPE_USERINFO} {GOOGLE_SCOPE_PROFILE}'
        params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': settings.GOOGLE_REDIRECT_URI,
        'scope': scope,
        'state': 'some_random_state_string_for_security', 
        'access_type': 'offline'
        }
        authorization_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        return authorization_url

    @staticmethod
    def handle_google_callback(code, state):
        token_request_data = {
            'code': code,
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,
            'grant_type': 'authorization_code'
        }
        token_response = requests.post('https://oauth2.googleapis.com/token', data=token_request_data)
        token_json = token_response.json()
        google_access_token = token_json.get('access_token')
        google_refresh_token = token_json.get('refresh_token')

        # 구버젼: 'https://www.googleapis.com/oauth2/v1/tokeninfo',
        userinfo_response = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={'Authorization': f'Bearer {google_access_token}'}
        )
        userinfo = userinfo_response.json()
        email = userinfo.get('email')
        name = userinfo.get('name')

        user = User.objects.filter(email=email).first()
        if user:
            return UserService.get_token(user)

        user = User.objects.create(
            email=userinfo.get('email'), 
            username=userinfo.get('name'), 
            profile_image=userinfo.get('picture')
        )
        return UserService.get_token(user)
