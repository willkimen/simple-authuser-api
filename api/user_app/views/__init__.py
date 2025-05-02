from .activate_account_views import activate_account, request_account_activation_code
from .change_email_views import change_email, request_email_change_code
from .profile_views import change_password, delete, detail, register, update
from .reset_password_views import request_reset_password_code, reset_password
from .token_views import (
    blacklist_token,
    obtain_token_pair,
    refresh_token_access,
    verify_token,
)
