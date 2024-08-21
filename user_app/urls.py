from django.urls import path

from .views import (
    activate_account,
    blacklist_jwt_access,
    blacklist_jwt_pair,
    blacklist_jwt_refresh,
    obtain_jwt_pair,
    refresh_jwt_access,
    register,
    send_email_to_activate_account,
    update,
)

urlpatterns = [
    # User
    path("users/", register, name="register"),
    path("users/", update, name="update"),
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
    # JWT
    path("jwt/pair/", obtain_jwt_pair, name="obtain_jwt_pair"),
    path("jwt/access/", refresh_jwt_access, name="refresh_jwt_access"),
    path("jwt/blacklist/pair/", blacklist_jwt_pair, name="blacklist_jwt_pair"),
    path("jwt/blacklist/access/", blacklist_jwt_access, name="blacklist_jwt_access"),
    path("jwt/blacklist/refresh/", blacklist_jwt_refresh, name="blacklist_jwt_refresh"),
]
