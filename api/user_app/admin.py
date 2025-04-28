from django.contrib import admin
from django.contrib.auth import get_user_model
from user_app import models

User = get_user_model()


@admin.register(User)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "first_name",
        "last_name",
        "email",
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined",
    )

    ordering = ("id",)
    list_per_page = 10


@admin.register(models.PendingAccountsModel)
class PendingAccountsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "first_reminder_at",
        "second_reminder_at",
        "activation_deadline",
        "user",
    )

    ordering = ("activation_deadline",)
    list_per_page = 10


@admin.register(models.UsersPendingDeletionNotificationModel)
class UsersPendingDeletionNotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "email")

    ordering = ("id",)
    list_per_page = 10


@admin.register(models.ValidTokenModel)
class ValidTokenAdmin(admin.ModelAdmin):
    list_display = ("id", "jti", "exp", "typ", "user_id")

    ordering = ("exp",)
    list_per_page = 10


@admin.register(models.BlacklistTokenModel)
class BlacklistTokenAdmin(admin.ModelAdmin):
    list_display = ("id", "jti", "exp", "typ", "user_id")

    ordering = ("exp",)
    list_per_page = 10


@admin.register(models.AccountActivationCodeModel)
class AccountActivationCodeAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "created_at", "expires_at", "user_id")

    ordering = ("expires_at",)
    list_per_page = 10


@admin.register(models.ChangeEmailCodeModel)
class ChangeEmailCodeAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "new_email", "created_at", "expires_at", "user_id")

    ordering = ("expires_at",)
    list_per_page = 10


@admin.register(models.ResetPasswordCodeModel)
class ResetPasswordCodeAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "created_at", "expires_at", "user_id")

    ordering = ("expires_at",)
    list_per_page = 10


def retry(modeladmin, request, queryset):
    """
    Attempts to re-execute selected Celery tasks from the Django Admin.

    For each selected task in the queryset, this method retrieves the original
    arguments and keyword arguments and tries to re-execute the task asynchronously.
    After the attempt, it displays success or error messages in the Admin interface.

    This feature makes it easier to manually retry failed tasks directly
    from the administration panel.

    Args:
        modeladmin: The ModelAdmin instance handling the action.
        request: The current HTTP request object.
        queryset: A queryset of selected failed tasks to retry.
    """

    retried = 0
    failed = 0

    for failed_task in queryset:
        try:
            failed_task.retry()
            retried += 1
        except Exception as e:
            failed += 1
            modeladmin.message_user(
                request,
                f"Error retrying task '{failed_task.task_name}' (ID: {failed_task.id}): {str(e)}",
                level="error",
            )

    if retried:
        modeladmin.message_user(
            request, f"{retried} task(s) retried successfully.", level="success"
        )

    if failed:
        modeladmin.message_user(
            request, f"{failed} task(s) failed to retry.", level="error"
        )


retry.short_description = "Retry selected tasks"


@admin.register(models.FailedTaskModel)
class FailedTaskAdmin(admin.ModelAdmin):
    """
    Admin interface for managing the `FailedTaskModel` and providing a
    UI for retrying failed tasks.

    This class configures the Django Admin interface to display failed tasks and allows
    administrators to retry them through the `retry` action.
    """

    list_display = ("id", "task_name", "task_id", "exception", "created_at")

    ordering = ("created_at",)
    list_per_page = 10
    actions = [retry]
