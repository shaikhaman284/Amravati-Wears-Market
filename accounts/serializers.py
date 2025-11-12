from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone', 'name', 'user_type', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserRegistrationSerializer(serializers.Serializer):
    firebase_token = serializers.CharField(required=True)
    name = serializers.CharField(required=True, max_length=255)
    user_type = serializers.ChoiceField(choices=['customer', 'seller'], default='customer')
    phone = serializers.CharField(required=True, max_length=15)

    def validate_phone(self, value):
        # Ensure phone starts with country code format
        if not value.startswith('+'):
            value = f'+91{value}'  # Default to India
        return value


class TokenVerificationSerializer(serializers.Serializer):
    firebase_token = serializers.CharField(required=True)