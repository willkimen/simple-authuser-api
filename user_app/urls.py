from django.urls import path

from .views import (
    activate_account,
    blacklist_token,
    obtain_jwt_pair,
    refresh_jwt_access,
    register,
    send_email_to_activate_account,
    update,
)

urlpatterns = [
    # ============= User Endpoints ====================
    # Endpoint to register a new user. Accepts a POST request with user data.
    path("users/register/", register, name="register"),
    # Endpoint to update an existing user. Accepts PATCH requests to modify user data.
    path("users/update/", update, name="update"),
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
    # Endpoint to obtain a JWT pair (access and refresh tokens) after successful login.
    path("jwt/pair/", obtain_jwt_pair, name="obtain_jwt_pair"),
    # Endpoint to refresh the access token using a valid refresh token.
    path("jwt/access/", refresh_jwt_access, name="refresh_jwt_access"),
    # Endpoint to add a token to the blacklist.
    path("jwt/blacklist/", blacklist_token, name="blacklist_token"),
]
