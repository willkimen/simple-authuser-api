from django.urls import path

from .views import register, update

urlpatterns = [
    path("users/", register, name="register"),
    path("users/<int:id>/", update, name="update"),
]
