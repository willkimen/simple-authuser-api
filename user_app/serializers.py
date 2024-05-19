from rest_framework import serializers
from .models import UserProfile


class RegisterSerializer(serializers.ModelSerializer):
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
