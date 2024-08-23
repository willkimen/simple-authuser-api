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
    # ============= User Endpoints ====================
    # Endpoint to register a new user. Accepts a POST request with user data.
    path("users/", register, name="register"),
    # Endpoint to update an existing user. Accepts PATCH requests to modify user data.
    path("users/", update, name="update"),
    # Endpoint to activate a user's account with a confirmation code sent via email. Accepts a POST request.
    path(
        "users/activate_account/",
        activate_account,
        name="activate_account",
    ),
    # Endpoint to send an activation email to the user. Accepts a POST request.
    path(
        "users/email/send_email_to_activate_account/",
        send_email_to_activate_account,
        name="send_email_to_activate_account",
    ),
    # =============== JWT Endpoints =================
    # Endpoint to obtain a JWT pair (access and refresh tokens) after successful login. Accepts a POST request.
    path("jwt/pair/", obtain_jwt_pair, name="obtain_jwt_pair"),
    # Endpoint to refresh the access token using a valid refresh token. Accepts a POST request.
    path("jwt/access/", refresh_jwt_access, name="refresh_jwt_access"),
    # Endpoint to add a JWT pair (access and refresh tokens) to the blacklist. Accepts a POST request.
    path("jwt/blacklist/pair/", blacklist_jwt_pair, name="blacklist_jwt_pair"),
    # Endpoint to add an access token to the blacklist. Accepts a POST request.
    path("jwt/blacklist/access/", blacklist_jwt_access, name="blacklist_jwt_access"),
    # Endpoint to add a refresh token to the blacklist. Accepts a POST request.
    path("jwt/blacklist/refresh/", blacklist_jwt_refresh, name="blacklist_jwt_refresh"),
]
