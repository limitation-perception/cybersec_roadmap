from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse
from rest_framework import serializers


class ValidationErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()
    errors = serializers.DictField(child=serializers.ListField(child=serializers.CharField()))


class DetailSerializer(serializers.Serializer):
    detail = serializers.CharField()


class AuthErrorSerializer(DetailSerializer):
    code = serializers.CharField(required=False)
    messages = serializers.ListField(child=serializers.DictField(), required=False)


def id_parameter(what):
    return OpenApiParameter("id", int, OpenApiParameter.PATH, description=f"{what} ID.")


def validation_error(**examples):
    return OpenApiResponse(
        ValidationErrorSerializer,
        description="Invalid data.",
        examples=[
            OpenApiExample(name, value={"detail": "Invalid data.", "errors": errors})
            for name, errors in examples.items()
        ],
    )


UNAUTHORIZED = OpenApiResponse(
    AuthErrorSerializer,
    description="Missing, invalid or expired token.",
    examples=[
        OpenApiExample("No token", value={"detail": "Authentication credentials were not provided."}),
        OpenApiExample(
            "Invalid token",
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
        description="Not found.",
        examples=[OpenApiExample("Not found", value={"detail": f"No {model} matches the given query."})],
    )


def conflict(description, detail):
    return OpenApiResponse(
        DetailSerializer,
        description=description,
        examples=[OpenApiExample("Has related objects", value={"detail": detail})],
    )


NO_CONTENT = OpenApiResponse(description="Deleted.")
