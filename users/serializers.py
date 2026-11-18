from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, max_length=128, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, max_length=128)
    email = serializers.EmailField(max_length=254)

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "password", "password_confirm"]

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return data

    def create(self, data):
        data.pop("password_confirm")
        return User.objects.create_user(**data)
