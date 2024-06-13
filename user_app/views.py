from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from user_app.serializers import UserSerializer

from .utils.email_service import send_activation_email

User = get_user_model()


@api_view(["POST"])
def register(request):
    """
    Registra um novo usuário.

    Args:
        request (Request): A instância do request contendo os dados do usuário.

    Returns:
        Response: Uma resposta contendo os dados do usuário registrado ou os erros de validação.

    Este endpoint registra um novo usuário no sistema. Se os dados fornecidos forem válidos,
    o usuário é criado e um email de ativação é enviado para o endereço de email fornecido.
    O usuário é inicialmente marcado como inativo até que ele ative sua conta através do email de ativação.
    """
    # Inicializa o serializer com os dados do request
    serializer = UserSerializer(data=request.data)

    # Verifica se os dados fornecidos são válidos
    if not serializer.is_valid():
        return Response(
            {"validation_errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )

    # Salva o usuário no banco de dados
    user = serializer.save()
    user.is_active = False  # Marca o usuário como inativo
    user.save()

    # Envia o email de ativação
    send_activation_email(user, request)

    return Response(
        {"user": serializer.data, "message": "User registered successfully"},
        status=status.HTTP_201_CREATED,
    )


@api_view(["PATCH"])
def update(request, id: int):
    try:
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        return Response(
            {"message": "User with id not found."}, status=status.HTTP_400_BAD_REQUEST
        )

    serializer = UserSerializer(instance=user, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(
            {"validation_errors": serializer.errors},
            status=status.status.HTTP_400_BAD_REQUEST,
        )

    serializer.save()
    return Response(
        {"user": serializer.data, "message": "User updated successfully."},
        status=status.HTTP_200_OK,
    )
