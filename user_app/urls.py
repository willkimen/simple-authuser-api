from django.urls import path

from .views import activate_account, register, update

urlpatterns = [
    path("users/", register, name="register"),
    path("users/<int:id>/", update, name="update"),
    path(
        "users/confirmation_register/",
        activate_account,
        name="confirmation_register",
    ),
]
