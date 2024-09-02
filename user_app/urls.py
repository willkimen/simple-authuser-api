from django.urls import path

from .views import (
    activate_account,
    blacklist_token,
    obtain_token_pair,
    refresh_token_access,
    register,
    send_email_to_activate_account,
    update,
    user_detail,
)

urlpatterns = [
    # ============= User Endpoints ====================
    # Endpoint to register a new user. Accepts a POST request with user data.
    path("user/register/", register, name="register"),
    # Endpoint to update an existing user. Accepts PATCH requests to modify user data.
    path("user/update/", update, name="update"),
    path("user/detail/", user_detail, name="detail"),
    # Endpoint to activate a user's account with a confirmation code sent via email. Accepts a POST request.
    path(
        "user/activate_account/",
        activate_account,
        name="activate_account",
    ),
    # Endpoint to send an activation email to the user. Accepts a POST request.
    path(
        "user/email/send_email_to_activate_account/",
        send_email_to_activate_account,
        name="send_email_to_activate_account",
    ),
    # =============== JWT Endpoints =================
    # Endpoint to obtain a JWT pair (access and refresh tokens) after successful login.
    path("token/pair/", obtain_token_pair, name="obtain_token_pair"),
    # Endpoint to refresh the access token using a valid refresh token.
    path("token/access/", refresh_token_access, name="refresh_token_access"),
    # Endpoint to add a token to the blacklist.
    path("token/blacklist/", blacklist_token, name="blacklist_token"),
]
