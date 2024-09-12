import importlib

token_utils_module_path = importlib.import_module("user_app.utils.token_utils").__name__

activate_account_view_path = importlib.import_module(
    "user_app.views.activate_account_view"
).__name__

crud_view_path = importlib.import_module("user_app.views.crud_view").__name__

change_email_view_path = importlib.import_module(
    "user_app.views.change_email_view"
).__name__

email_service_module_path = importlib.import_module(
    "user_app.utils.email_service"
).__name__
