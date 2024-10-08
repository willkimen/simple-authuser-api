from django.contrib import admin
from django.contrib.auth import get_user_model

from user_app import models

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "first_name",
        "last_name",
        "email",
        "is_active",
        "is_staff",
        "is_superuser",
    )

    ordering = ("id",)
    list_per_page = 10


@admin.register(models.ValidTokenModel)
class ValidTokenAdmin(admin.ModelAdmin):
    list_display = ("id", "jti", "exp", "typ", "user_id")

    ordering = ("id",)
    list_per_page = 10


@admin.register(models.BlacklistTokenModel)
class BlacklistTokenAdmin(admin.ModelAdmin):
    list_display = ("id", "jti", "exp", "typ", "user_id")

    ordering = ("id",)
    list_per_page = 10


@admin.register(models.AccountActivationCodeModel)
class AccountActivationCodeAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "created_at", "expires_at", "user_id")

    ordering = ("id",)
    list_per_page = 10


@admin.register(models.ChangeEmailCodeModel)
class ChangeEmailCodeCodeAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "created_at", "expires_at", "user_id", "new_email")

    ordering = ("id",)
    list_per_page = 10


@admin.register(models.ResetPasswordCodeModel)
class ResetPasswordCodeAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "created_at", "expires_at", "user_id")

    ordering = ("id",)
    list_per_page = 10
