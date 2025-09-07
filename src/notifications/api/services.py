# src/notifications/api/services.py
from typing import Iterable, Optional
from django.contrib.auth import get_user_model
from django.db import transaction
from src.notifications.models import Notification  # ajuste se necessário

User = get_user_model()


def create_notification(
    *,
    recipient: User,
    title: str,
    message: str = "",
    link: Optional[str] = None,
    kind: Optional[str] = None,
) -> Notification:
    """
    Cria uma notificação para um usuário.
    """
    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message or "",
        link=link,
        kind=kind,
    )


@transaction.atomic
def bulk_notify(
    recipients: Iterable[User],
    *,
    title: str,
    message: str = "",
    link: Optional[str] = None,
    kind: Optional[str] = None,
) -> int:
    """
    Cria notificações em lote. Retorna a quantidade criada.
    """
    payloads = [
        Notification(
            recipient=r,
            title=title,
            message=message or "",
            link=link,
            kind=kind,
        )
        for r in recipients
    ]
    created = Notification.objects.bulk_create(payloads)
    return len(created)


def notify_new_customer(customer_user: User):
    """
    Exemplo de gatilho: novo 'customer' registrado -> notificar employees.
    Ajuste o filtro conforme seu schema (Profile/user_role).
    """
    recipients = User.objects.filter(profile__user_role__user_role="employee")

    title = "New customer registered"
    message = f"{customer_user.get_full_name() or customer_user.email} has signed up."
    link = "/customers"
    kind = "customer_signup"

    return bulk_notify(recipients, title=title, message=message, link=link, kind=kind)
