# src/notifications/api/views.py
from django.forms.models import model_to_dict
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication

# JWT é opcional; usa se estiver instalado
try:
    from rest_framework_simplejwt.authentication import JWTAuthentication
    AUTH_CLASSES = (SessionAuthentication, JWTAuthentication)
except Exception:
    AUTH_CLASSES = (SessionAuthentication,)

from src.notifications.models import Notification  # ajuste se o caminho do model for diferente


def serialize_notification(n: Notification) -> dict:
    """
    Serializa Notification usando model_to_dict e inclui created_at.
    """
    data = model_to_dict(
        n,
        fields=["id", "title", "message", "link", "kind", "is_read"]
    )
    data["created_at"] = n.created_at.isoformat() if n.created_at else None
    return data


class NotificationCountView(APIView):
    """
    GET /api/notifications/count/  -> { "unread": <int> }
    """
    authentication_classes = AUTH_CLASSES
    permission_classes = [IsAuthenticated]

    def get(self, request):
        unread = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return Response({"unread": unread})


class NotificationListView(APIView):
    """
    GET /api/notifications/?unread=1|0&limit=20&offset=0
    Retorna results + paginação básica.
    """
    authentication_classes = AUTH_CLASSES
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Notification.objects.filter(recipient=request.user).order_by("-created_at")

        # filtros opcionais
        unread = request.query_params.get("unread")
        if unread is not None:
            # unread=1 => não lidas; unread=0 => lidas
            qs = qs.filter(is_read=(unread == "0"))

        # paginação simples
        try:
            limit = int(request.query_params.get("limit", 20))
        except ValueError:
            limit = 20
        limit = max(1, min(limit, 100))

        try:
            offset = int(request.query_params.get("offset", 0))
        except ValueError:
            offset = 0
        offset = max(0, offset)

        total = qs.count()
        items = [serialize_notification(n) for n in qs[offset: offset + limit]]

        return Response({
            "results": items,
            "count": total,
            "limit": limit,
            "offset": offset,
        })


class NotificationMarkReadView(APIView):
    """
    PATCH /api/notifications/<pk>/read/ -> marca como lida (apenas do próprio usuário).
    """
    authentication_classes = AUTH_CLASSES
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk: int):
        try:
            notif = Notification.objects.get(pk=pk)
        except Notification.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)

        if notif.recipient_id != request.user.id:
            return Response({"detail": "Forbidden."}, status=403)

        if not notif.is_read:
            notif.is_read = True
            notif.save(update_fields=["is_read"])

        return Response({"ok": True, "id": notif.id, "is_read": notif.is_read})
