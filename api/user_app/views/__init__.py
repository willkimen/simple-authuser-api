from .activate_account_views import activate_account, request_account_activation_code
from .change_email_views import change_email, request_email_change_code
from .profile_views import change_password, delete, register, update, detail
from .reset_password_views import reset_password, request_reset_password_code
from .token_views import (
    blacklist_token,
    obtain_token_pair,
    refresh_token_access,
    verify_token,
)
