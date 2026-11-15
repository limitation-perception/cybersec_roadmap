"""Опис для OpenAPI-документації (drf-spectacular): формати помилок, типові відповіді й приклади.

Логіка API ці серіалізатори не використовує — вони лише описують, що повертають views.
"""
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse
from rest_framework import serializers


class ValidationErrorSerializer(serializers.Serializer):
    detail = serializers.CharField(help_text='Завжди "Invalid data."')
    errors = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()),
        help_text="Помилки по кожному полю: назва поля → список повідомлень.",
    )


class DetailSerializer(serializers.Serializer):
    detail = serializers.CharField(help_text="Зрозуміле повідомлення про помилку.")


class AuthErrorSerializer(DetailSerializer):
    code = serializers.CharField(required=False, help_text='"token_not_valid", якщо токен невалідний чи прострочений.')
    messages = serializers.ListField(child=serializers.DictField(), required=False, help_text="Подробиці про токен.")


def id_parameter(what):
    return OpenApiParameter("id", int, OpenApiParameter.PATH, description=f"ID {what}.")


def validation_error(**examples):
    """400: приклади передаються як назва → errors."""
    return OpenApiResponse(
        ValidationErrorSerializer,
        description="Невалідні дані. Помилки повертаються окремо для кожного поля.",
        examples=[
            OpenApiExample(name, value={"detail": "Invalid data.", "errors": errors})
            for name, errors in examples.items()
        ],
    )


UNAUTHORIZED = OpenApiResponse(
    AuthErrorSerializer,
    description="Немає заголовка `Authorization`, або access токен невалідний чи прострочений.",
    examples=[
        OpenApiExample("Без токена", value={"detail": "Authentication credentials were not provided."}),
        OpenApiExample(
            "Невалідний або прострочений токен",
            value={
                "detail": "Given token not valid for any token type",
                "code": "token_not_valid",
                "messages": [{"token_class": "AccessToken", "token_type": "access", "message": "Token is invalid"}],
            },
        ),
    ],
)


def not_found(model):
    return OpenApiResponse(
        DetailSerializer,
        description="Об'єкта з таким `id` не існує.",
        examples=[OpenApiExample("Не знайдено", value={"detail": f"No {model} matches the given query."})],
    )


def conflict(description, detail):
    return OpenApiResponse(
        DetailSerializer,
        description=description,
        examples=[OpenApiExample("Є пов'язані записи", value={"detail": detail})],
    )


NO_CONTENT = OpenApiResponse(description="Видалено, тіла відповіді немає.")
