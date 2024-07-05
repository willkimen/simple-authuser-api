from django.urls import path

from .views import confirmation_register, register, update

urlpatterns = [
    path("users/", register, name="register"),
    path("users/<int:id>/", update, name="update"),
    path(
        "users/confirmation_register/",
        confirmation_register,
        name="confirmation_register",
    ),
]
