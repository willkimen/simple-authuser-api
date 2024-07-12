from django.urls import path

from .views import activate_account, register, update

urlpatterns = [
    path("users/", register, name="register"),
    path("users/<int:id>/", update, name="update"),
    path(
        "users/activate_account/",
        activate_account,
        name="activate_account",
    ),
]
