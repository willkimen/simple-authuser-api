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
    # ============= account Endpoints ====================
    path("account/register/", register, name="register"),
    path("account/update/", update, name="update"),
    path("account/detail/", detail, name="detail"),
    path("account/delete/", delete, name="delete"),
    path("account/change_password/", change_password, name="change_password"),
    # Activate account account
    path(
        "account/email/send_code/activate_account/",
        request_account_activation_code,
        name="request_account_activation_code",
    ),
    path("account/code/activate/", activate_account, name="activate_account"),
    # Change account email
    path(
        "account/email/send_code/change_email/",
        request_email_change_code,
        name="request_email_change_code",
    ),
    path("account/code/change_email/", change_email, name="change_email"),
    # Reset account password
    path(
        "account/email/send_code/reset_password/",
        request_reset_password_code,
        name="request_reset_password_code",
    ),
    path("account/code/reset_password/", reset_password, name="reset_password"),
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
