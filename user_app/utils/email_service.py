import threading

from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpRequest
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from ..utils.token import user_active_generate_token


class EmailThread(threading.Thread):
    """
    Classe para enviar email em uma nova thread.

    Args:
        email (EmailMessage): A instância do email a ser enviado.

    Métodos:
        run(): Envia o email.
    """

    def __init__(self, email: EmailMessage) -> None:
        super().__init__()
        self.email = email

    def run(self) -> None:
        """
        Envia o email quando a thread é iniciada.
        """
        self.email.send()


def send_activation_email(user: User, request: HttpRequest) -> None:
    """
    Envia um email de ativação para o usuário.

    Args:
        user (User): A instância do usuário para quem o email será enviado.
        request (HttpRequest): A instância do request atual para obter o site atual.

    Esta função cria o conteúdo do email de ativação da conta,incluindo um link de ativação com um token seguro.
    O email é então enviado em uma nova thread para evitar bloquear o processo principal.
    """
    current_site = get_current_site(request)  # Obtém o site atual a partir do request
    email_subject = "Activate your account"  # Assunto do email
    uid = urlsafe_base64_encode(
        force_bytes(user.id)
    )  # Codifica o ID do usuário em base64
    token = user_active_generate_token.make_token(
        user
    )  # Gera um token de ativação para o usuário
    end_point = reverse("confirmation_register", kwargs={"id": uid, "token": token})

    activation_link = (
        f"http://{current_site.domain}/api/v1/{end_point}"  # Cria o link de ativação
    )

    email_body = f"""
    Hi {user.first_name} {user.last_name},

    Please click the link below to activate your account:

    {activation_link}

    If you did not request this email, please ignore it.
    """

    email = EmailMessage(
        subject=email_subject, body=email_body, to=[user.email]
    )  # Cria a mensagem de email
    email_thread = EmailThread(email)  # Cria uma nova thread para enviar o email
    email_thread.start()  # Inicia a thread para enviar o email
