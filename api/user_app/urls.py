from django.urls import path

from .views import (
    activate_account,
    blacklist_token,
    change_email,
    change_password,
    delete,
    detail,
    obtain_token_pair,
    refresh_token_access,
    register,
    request_account_activation_code,
    request_email_change_code,
    request_reset_password_code,
    reset_password,
    update,
    verify_token,
)

urlpatterns = [
    # ============= User Endpoints ====================
    path("user/profile/register/", register, name="register"),
    path("user/profile/update/", update, name="update"),
    path("user/profile/detail/", detail, name="detail"),
    path("user/profile/delete/", delete, name="delete"),
    path("user/profile/change_password/", change_password, name="change_password"),
    # Activate user account
    path(
        "user/email/send_code/activate_account/",
        request_account_activation_code,
        name="request_account_activation_code",
    ),
    path("user/code/activate/", activate_account, name="activate_account"),
    # Change user email
    path(
        "user/email/send_code/change_email/",
        request_email_change_code,
        name="request_email_change_code",
    ),
    path("user/code/change_email/", change_email, name="change_email"),
    # Reset user password
    path(
        "user/email/send_code/reset_password/",
        request_reset_password_code,
        name="request_reset_password_code",
    ),
    path("user/code/reset_password/", reset_password, name="reset_password"),
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
