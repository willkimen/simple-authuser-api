from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from user_app.serializers import UserSerializer, UserUpdateSerializer

User = get_user_model()


@api_view(["POST"])
def register(request):
    serializer = UserSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"validation_errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )

    user = serializer.save()
    return Response(
        {"user_id": user.id, "message": "User registered successfully"},
        status=status.HTTP_201_CREATED,
    )


@api_view(["PATCH"])
def update(request, id: int):
    try:
        user = User.objects.get(id=id)
    except ObjectDoesNotExist:
        return Response(
            {"message": "User with id not found."}, status=status.HTTP_400_BAD_REQUEST
        )

    serializer = UserUpdateSerializer(instance=user, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(
            {"validation_errors": serializer.errors},
            status=status.status.HTTP_400_BAD_REQUEST,
        )

    serializer.save()
    return Response(
        {"message": "User updated successfully."}, status=status.HTTP_200_OK
    )
