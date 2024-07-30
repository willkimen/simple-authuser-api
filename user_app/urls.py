from django.urls import path

from .views import (
    activate_account,
    login,
    register,
    send_email_to_activate_account,
    update,
)

urlpatterns = [
    path("users/", register, name="register"),
    path("users/<int:id>/", update, name="update"),
    path(
        "users/activate_account/",
        activate_account,
        name="activate_account",
    ),
    path(
        "users/email/send_email_to_activate_account/",
        send_email_to_activate_account,
        name="send_email_to_activate_account",
    ),
    path("users/login/", login, name="login"),
]
