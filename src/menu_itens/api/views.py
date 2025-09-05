from django.forms.models import model_to_dict
from django.db.models import Q, Prefetch
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication

# JWT é opcional; se não estiver instalado, seguimos só com Session.
try:
    from rest_framework_simplejwt.authentication import JWTAuthentication
    AUTH_CLASSES = (SessionAuthentication, JWTAuthentication)
except Exception:
    AUTH_CLASSES = (SessionAuthentication,)

from ..models import MenuItem, RoleMenuItem
from src.users.models import Profile  # ajuste se seu Profile estiver noutro módulo


def _visible_children_for(item, user_type_id, user_role_id):
    """
    Filhos visíveis para o user_type OU user_role, ordenados.
    Ignora vínculos 'globais' (onde user_type e user_role são ambos NULL).
    """
    return (
        item.children.filter(is_active=True)
        .filter(
            Q(role_links__is_visible=True)
            & (
                Q(role_links__user_type_id=user_type_id)
                | Q(role_links__user_role_id=user_role_id)
            )
            & (  # blindagem contra links sem type/role definido
                Q(role_links__user_type__isnull=False)
                | Q(role_links__user_role__isnull=False)
            )
        )
        .order_by("role_links__order", "id")
        .distinct()
    )


def _serialize_item(item, user_type_id, user_role_id):
    """
    Serializa um MenuItem e seus filhos permitidos usando model_to_dict.
    """
    data = model_to_dict(item, fields=["key", "label", "icon", "path"])
    children_qs = _visible_children_for(item, user_type_id, user_role_id)
    data["children"] = [_serialize_item(child, user_type_id, user_role_id) for child in children_qs]
    return data


class SidebarView(APIView):
    """
    Retorna o menu filtrado por Profile.user_type OU Profile.user_role.
    Requer autenticação por sessão (login no /admin) e/ou JWT.
    """
    authentication_classes = AUTH_CLASSES
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Garante que temos Profile (superuser antigo pode não ter sido criado pelo signal).
        profile = getattr(request.user, "profile", None)
        if request.user.is_authenticated and profile is None:
            # Para não travar seus testes, criamos automaticamente.
            profile, _ = Profile.objects.get_or_create(user=request.user)

        user_type_id = getattr(getattr(profile, "user_type", None), "id", None)
        user_role_id = getattr(getattr(profile, "user_role", None), "id", None)

        roots = (
            MenuItem.objects.filter(parent__isnull=True, is_active=True)
            .filter(
                Q(role_links__is_visible=True)
                & (
                    Q(role_links__user_type_id=user_type_id)
                    | Q(role_links__user_role_id=user_role_id)
                )
                & (  # blindagem contra links sem type/role definido
                    Q(role_links__user_type__isnull=False)
                    | Q(role_links__user_role__isnull=False)
                )
            )
            .order_by("role_links__order", "id")
            .distinct()
            .prefetch_related(
                Prefetch("children", queryset=MenuItem.objects.filter(is_active=True)),
                Prefetch("role_links", queryset=RoleMenuItem.objects.all()),
            )
        )

        items = [_serialize_item(root, user_type_id, user_role_id) for root in roots]

        return Response({
            "user_type": getattr(getattr(profile, "user_type", None), "user_type", None),
            "user_role": getattr(getattr(profile, "user_role", None), "user_role", None),
            "items": items
        })
