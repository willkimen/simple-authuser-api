from rest_framework import serializers
from .models import UserProfile
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password_confirmation = serializers.CharField()

    class Meta:
        model = UserProfile
        fields = [
            'first_name',
            'last_name',
            'email',
            'password',
            'password_confirmation',
        ]

        extra_kwargs = {
            'password': {'write_only': True},
            'password_confirmation': {'write_only': True},
        }

    def create(self, validated_data):
        validated_data.pop('password_confirmation', None)
        return User.objects.create_user(**validated_data)

    def validate(self, data):
        if data.get('password') != data.get('password_confirmation'):
            raise serializers.ValidationError(detail={'password_confirmation': 'Password do not match'})

        return data

    def validate_password(self, password):
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError(detail=e)

        return password
