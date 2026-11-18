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
        summary="Register",
        auth=[],
        request=RegisterSerializer,
        examples=[
            OpenApiExample(
                "New user",
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
                examples=[
                    OpenApiExample(
                        "Created",
                        value={"id": 1, "username": "alice", "first_name": "Alice", "last_name": "", "email": "alice@example.com"},
                    )
                ],
            ),
            400: validation_error(
                **{
                    "Invalid email, weak password": {
                        "email": ["Enter a valid email address."],
                        "password": [
                            "This password is too short. It must contain at least 8 characters.",
                            "This password is too common.",
                            "This password is entirely numeric.",
                        ],
                    },
                    "Passwords mismatch": {"password_confirm": ["Passwords do not match."]},
                    "Username taken": {"username": ["A user with that username already exists."]},
                }
            ),
        },
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
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
    summary="Log in",
    examples=[OpenApiExample("Login", value={"username": "alice", "password": "Str0ng-Pass!"}, request_only=True)],
    responses={
        200: OpenApiResponse(
            TokenObtainPairSerializer,
            examples=[OpenApiExample("Tokens", value={"refresh": REFRESH, "access": ACCESS})],
        ),
        400: OpenApiResponse(
            OpenApiTypes.OBJECT,
            examples=[OpenApiExample("Missing fields", value={"username": ["This field is required."], "password": ["This field is required."]})],
        ),
        401: OpenApiResponse(
            DetailSerializer,
            examples=[OpenApiExample("Wrong credentials", value={"detail": "No active account found with the given credentials"})],
        ),
    },
)
class LoginView(TokenObtainPairView):
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
    summary="Refresh access token",
    examples=[OpenApiExample("Refresh", value={"refresh": REFRESH}, request_only=True)],
    responses={
        200: OpenApiResponse(TokenRefreshSerializer, examples=[OpenApiExample("New access", value={"access": ACCESS})]),
        401: OpenApiResponse(
            AuthErrorSerializer,
            examples=[OpenApiExample("Invalid refresh", value={"detail": "Token is invalid", "code": "token_not_valid"})],
        ),
    },
)
class RefreshView(TokenRefreshView):
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
