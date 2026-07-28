from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.validators import UnicodeUsernameValidator
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "avatar",
            "banner_image",
            "banner_style",
            "phone",
            "bio",
            "last_seen_at",
            "date_joined",
        )
        read_only_fields = fields


class UserPublicSerializer(serializers.ModelSerializer):
    """Minimal profile for chat member lists / user lookup."""

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "banner_image",
            "banner_style",
            "phone",
            "bio",
            "last_seen_at",
        )
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")
        read_only_fields = ("id",)

    def create(self, validated_data: dict) -> User:
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )


class MeUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        required=False,
        max_length=150,
        validators=[UnicodeUsernameValidator()],
    )
    banner_style = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "avatar",
            "banner_image",
            "banner_style",
            "phone",
            "bio",
        )
        read_only_fields = ("id",)

    def validate_username(self, value: str) -> str:
        cleaned = value.lstrip("@").strip()
        if not cleaned:
            raise serializers.ValidationError("Username cannot be empty.")
        qs = User.objects.filter(username__iexact=cleaned)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This username is already taken.")
        return cleaned

    def validate_banner_style(self, value: object) -> object:
        if isinstance(value, str):
            import json

            raw = value.strip()
            if not raw:
                return None
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise serializers.ValidationError("Invalid banner_style JSON.") from exc
        if value is None:
            return None
        if not isinstance(value, dict):
            raise serializers.ValidationError("banner_style must be an object.")
        return value

    def update(self, instance: User, validated_data: dict) -> User:
        # Uploading a custom banner clears generated style; generating style clears image.
        if validated_data.get("banner_image"):
            validated_data["banner_style"] = None
        if validated_data.get("banner_style") is not None:
            if instance.banner_image:
                instance.banner_image.delete(save=False)
            instance.banner_image = None
            validated_data.pop("banner_image", None)
            # Ensure DB column cleared on save.
            instance.save(update_fields=["banner_image"])
        return super().update(instance, validated_data)
