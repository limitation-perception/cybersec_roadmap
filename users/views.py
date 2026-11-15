import logging

from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from roadmap.schema import AuthErrorSerializer, DetailSerializer, validation_error
from .serializers import RegisterSerializer

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"],
        summary="Реєстрація",
        description=(
            "Обов'язкові поля: `username`, `email`, `password`, `password_confirm`. "
            "Пароль: мінімум 8 символів, не надто поширений і не лише з цифр. "
            "У базі пароль зберігається лише як хеш і у відповідь не повертається."
        ),
        auth=[],
        request=RegisterSerializer,
        examples=[
            OpenApiExample(
                "Новий користувач",
                value={
                    "username": "alice",
                    "first_name": "Alice",
                    "last_name": "",
                    "email": "alice@example.com",
                    "password": "Str0ng-Pass!",
                    "password_confirm": "Str0ng-Pass!",
                },
                request_only=True,
            )
        ],
        responses={
            201: OpenApiResponse(
                RegisterSerializer,
                description="Користувача створено.",
                examples=[
                    OpenApiExample(
                        "Створено",
                        value={"id": 1, "username": "alice", "first_name": "Alice", "last_name": "", "email": "alice@example.com"},
                    )
                ],
            ),
            400: validation_error(
                **{
                    "Невалідний email і слабкий пароль": {
                        "email": ["Enter a valid email address."],
                        "password": [
                            "This password is too short. It must contain at least 8 characters.",
                            "This password is too common.",
                            "This password is entirely numeric.",
                        ],
                    },
                    "Паролі не збігаються": {"password_confirm": ["Passwords do not match."]},
                    "Ім'я зайняте": {"username": ["A user with that username already exists."]},
                }
            ),
        },
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            # Лише назви полів: значення (пароль, email) у лог не пишемо.
            logger.warning("Registration rejected: invalid fields %s", sorted(serializer.errors))
            return Response(
                {"detail": "Invalid data.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = serializer.save()
        logger.info("User registered: id=%s username=%r", user.id, user.username)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


ACCESS = "eyJhbGciOiJIUzI1NiIs..."
REFRESH = "eyJhbGciOiJIUzI1NiIs..."


@extend_schema(
    tags=["Auth"],
    summary="Логін: отримати access і refresh токени",
    description=(
        "`access` живе 15 хвилин і передається в заголовку `Authorization: Bearer <access>`. "
        "`refresh` живе 1 день і потрібен лише для `POST /auth/refresh`."
    ),
    examples=[OpenApiExample("Логін", value={"username": "alice", "password": "Str0ng-Pass!"}, request_only=True)],
    responses={
        200: OpenApiResponse(
            TokenObtainPairSerializer,
            examples=[OpenApiExample("Токени", value={"refresh": REFRESH, "access": ACCESS})],
        ),
        400: OpenApiResponse(
            OpenApiTypes.OBJECT,
            description="Не передано `username` або `password`. Формат від simplejwt: поля одразу в корені, без `detail`.",
            examples=[OpenApiExample("Порожні поля", value={"username": ["This field is required."], "password": ["This field is required."]})],
        ),
        401: OpenApiResponse(
            DetailSerializer,
            description="Неправильне ім'я користувача або пароль.",
            examples=[OpenApiExample("Неправильні дані", value={"detail": "No active account found with the given credentials"})],
        ),
    },
)
class LoginView(TokenObtainPairView):
    # Пароль і видані токени в лог не потрапляють — лише username і результат.
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        try:
            response = super().post(request, *args, **kwargs)
        except AuthenticationFailed:
            logger.warning("Failed login: username=%r", username)
            raise
        except ValidationError:
            logger.warning("Login rejected: username or password not provided")
            raise
        logger.info("User logged in: username=%r", username)
        return response


@extend_schema(
    tags=["Auth"],
    summary="Отримати новий access токен",
    description="Викликайте, коли access прострочився (API відповідає 401). Коли прострочиться і refresh — потрібен новий логін.",
    examples=[OpenApiExample("Refresh", value={"refresh": REFRESH}, request_only=True)],
    responses={
        200: OpenApiResponse(TokenRefreshSerializer, examples=[OpenApiExample("Новий access", value={"access": ACCESS})]),
        401: OpenApiResponse(
            AuthErrorSerializer,
            description="Refresh токен невалідний або прострочений.",
            examples=[OpenApiExample("Невалідний refresh", value={"detail": "Token is invalid", "code": "token_not_valid"})],
        ),
    },
)
class RefreshView(TokenRefreshView):
    # Сам токен у лог не пишемо — лише факт оновлення чи відмови.
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
        except AuthenticationFailed:
            logger.warning("Token refresh failed: refresh token is invalid or expired")
            raise
        except ValidationError:
            logger.warning("Token refresh rejected: refresh token not provided")
            raise
        logger.debug("Access token refreshed")
        return response
