from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .cookies import (
    clear_refresh_cookie,
    get_refresh_from_request,
    set_refresh_cookie,
)
from .serializers import (
    MeUpdateSerializer,
    RegisterSerializer,
    UserPublicSerializer,
    UserSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    authentication_classes = []
    throttle_scope = "auth"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        response = Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                # Refresh also returned for non-browser clients; browser should
                # prefer the HttpOnly cookie and may ignore this field.
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )
        set_refresh_cookie(response, str(refresh))
        return response


class CookieTokenObtainPairView(TokenObtainPairView):
    """Login: issue JWT pair and set refresh HttpOnly cookie."""

    throttle_scope = "auth"

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200 and "refresh" in response.data:
            set_refresh_cookie(response, response.data["refresh"])
        return response


class CookieTokenRefreshView(TokenRefreshView):
    """Refresh access token using body.refresh or the HttpOnly cookie."""

    throttle_scope = "auth"

    def post(self, request, *args, **kwargs):
        data = {}
        if hasattr(request.data, "items"):
            data.update(request.data)
        if not data.get("refresh"):
            cookie_refresh = get_refresh_from_request(request)
            if cookie_refresh:
                data["refresh"] = cookie_refresh

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        access = serializer.validated_data["access"]
        response_data = {"access": str(access)}
        refresh = serializer.validated_data.get("refresh")
        if refresh:
            response_data["refresh"] = str(refresh)
        response = Response(response_data, status=status.HTTP_200_OK)
        if refresh:
            set_refresh_cookie(response, str(refresh))
        return response


class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return MeUpdateSerializer
        return UserSerializer


class UserDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserPublicSerializer
    queryset = User.objects.filter(is_active=True)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = get_refresh_from_request(request) or request.data.get("refresh")
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except (TokenError, InvalidToken, AttributeError):
                # Blacklist app may be disabled; still clear cookie.
                pass
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_refresh_cookie(response)
        return response
