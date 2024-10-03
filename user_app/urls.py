from django.urls import path

from .views import (
    activate_account,
    blacklist_token,
    change_password,
    change_user_email,
    delete,
    obtain_token_pair,
    refresh_token_access,
    register,
    reset_password,
    send_code_to_activate_account,
    send_code_to_email_change,
    send_code_to_reset_password,
    update,
    user_detail,
    verify_token,
)

urlpatterns = [
    # ============= User Endpoints ====================
    path("user/register/", register, name="register"),
    path("user/update/", update, name="update"),
    path("user/detail/", user_detail, name="detail"),
    path("user/delete/", delete, name="delete"),
    # Change user password
    path("user/change_passoword/", change_password, name="change_password"),
    # Activate user account
    path(
        "user/activate/",
        activate_account,
        name="activate_account",
    ),
    path(
        "user/email/send_code/activate_account/",
        send_code_to_activate_account,
        name="send_code_to_activate_account",
    ),
    # Change user email
    path(
        "user/email/send_code/change_email/",
        send_code_to_email_change,
        name="send_code_to_email_change",
    ),
    path(
        "user/change_email/",
        change_user_email,
        name="change_user_email",
    ),
    # Reset user password
    path(
        "user/send_code/reset_password/",
        send_code_to_reset_password,
        name="send_code_to_reset_password",
    ),
    path(
        "user/reset_password/",
        reset_password,
        name="reset_password",
    ),
    # =============== JWT Endpoints =================
    # Endpoint to obtain a JWT pair (access and refresh tokens) after successful login.
    path("token/pair/", obtain_token_pair, name="obtain_token_pair"),
    # Endpoint to refresh the access token using a valid refresh token.
    path("token/access/", refresh_token_access, name="refresh_token_access"),
    # Endpoint to add a token to the blacklist.
    path("token/blacklist/", blacklist_token, name="blacklist_token"),
    # Endpoint to verify token.
    path("token/verify/", verify_token, name="verify_token"),
]
