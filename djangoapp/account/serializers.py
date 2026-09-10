from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


class SignUpSerializer(serializers.ModelSerializer):
    """
    Un serializer fait le lien entre le modèle User et le JSON envoyé/reçu.
    Équivalent d'un Form, mais pensé pour les API.
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "password2"]

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    """Utilisé pour renvoyer les infos de l'utilisateur connecté (sans le mot de passe)."""
    class Meta:
        model = User
        fields = ["id", "username", "email"]