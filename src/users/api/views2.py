# src/users/api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from src.users.models import Profile, UserRole, UserType

User = get_user_model()


# ---------------------------------------------------------------------
# Users (lista + criação)
# ---------------------------------------------------------------------
class UsersAPIView(APIView):
    def get(self, request):
        users = (
            User.objects.select_related("profile")
            .order_by("-id")
            .values(
                "id", "username", "email", "first_name", "last_name", "is_active",
                "date_joined", "profile__id", "profile__company_id",
                "profile__user_role_id", "profile__user_type_id",
                "profile__phone_number", "profile__coverageType", "profile__insuranceCoverage",
            )[:200]
        )
        return Response(list(users))

    def post(self, request):
        # cria User
        u = User.objects.create_user(
            username=request.data.get("username") or request.data.get("email"),
            email=request.data.get("email"),
            password=request.data.get("password"),
            first_name=request.data.get("first_name"),
            last_name=request.data.get("last_name"),
            is_active=bool(request.data.get("is_active", True)),
        )
        # cria Profile básico (campos diretos por id)
        Profile.objects.get_or_create(user=u, defaults={
            "first_name": request.data.get("first_name"),
            "last_name": request.data.get("last_name"),
            "email": request.data.get("email"),
            "phone_number": request.data.get("phone_number"),
            "company_id": request.data.get("company_id"),
            "user_role_id": request.data.get("user_role_id"),
            "user_type_id": request.data.get("user_type_id"),
            "coverageType": request.data.get("coverageType"),
            "insuranceCoverage": request.data.get("insuranceCoverage"),
        })
        return Response()  # no-ops: no payload, no status custom, igual ao exemplo


# ---------------------------------------------------------------------
# User detail (GET/PATCH/DELETE)
# ---------------------------------------------------------------------
class UserDetailAPIView(APIView):
    def get(self, request, pk):
        u = get_object_or_404(User.objects.select_related("profile"), pk=pk)
        p = getattr(u, "profile", None)
        data = {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "is_active": u.is_active,
            "date_joined": u.date_joined,
            "last_login": u.last_login,
            "profile": {
                "id": getattr(p, "id", None),
                "phone_number": getattr(p, "phone_number", None),
                "company_id": getattr(p, "company_id", None),
                "user_role_id": getattr(p, "user_role_id", None),
                "user_type_id": getattr(p, "user_type_id", None),
                "coverageType": getattr(p, "coverageType", None),
                "insuranceCoverage": getattr(p, "insuranceCoverage", None),
                "email": getattr(p, "email", None),
                "first_name": getattr(p, "first_name", None),
                "last_name": getattr(p, "last_name", None),
            } if p else None,
        }
        return Response(data)

    def patch(self, request, pk):
        # atualiza campos do User que vierem no payload
        user_fields = ["username", "email", "first_name", "last_name", "is_active"]
        user_payload = {k: request.data[k] for k in user_fields if k in request.data}
        if "password" in request.data and request.data["password"]:
            u = get_object_or_404(User, pk=pk)
            u.set_password(request.data["password"])
            if user_payload:
                for k, v in user_payload.items():
                    setattr(u, k, v)
            u.save()
        else:
            if user_payload:
                User.objects.filter(pk=pk).update(**user_payload)

        # atualiza Profile por user_id com ids diretos e campos simples
        profile_fields = [
            "first_name", "last_name", "email", "phone_number",
            "company_id", "user_role_id", "user_type_id",
            "coverageType", "insuranceCoverage",
        ]
        profile_payload = {k: request.data[k] for k in profile_fields if k in request.data}
        if profile_payload:
            Profile.objects.filter(user_id=pk).update(**profile_payload)

        return Response()  # enxuto

    def delete(self, request, pk):
        get_object_or_404(User, pk=pk).delete()
        return Response(status=204)


# ---------------------------------------------------------------------
# Listas simples (roles e types)
# ---------------------------------------------------------------------
class UserRolesAPIView(APIView):
    def get(self, request):
        roles = UserRole.objects.all().order_by("id").values("id", "user_role")
        return Response(list(roles))


class UserTypesAPIView(APIView):
    def get(self, request):
        types = UserType.objects.all().order_by("id").values("id", "user_type")
        return Response(list(types))


# ---------------------------------------------------------------------
# Auth helpers mínimos (session info + logout)
# ---------------------------------------------------------------------
class AuthSessionAPIView(APIView):
    def get(self, request):
        u = request.user
        p = getattr(u, "profile", None)
        return Response({
            "user": {
                "id": getattr(u, "id", None),
                "email": getattr(u, "email", None),
                "first_name": getattr(u, "first_name", None),
                "last_name": getattr(u, "last_name", None),
            },
            "profile_id": getattr(p, "id", None),
        })


class AuthLogoutAPIView(APIView):
    def post(self, request):
        try:
            if hasattr(request, "session"):
                request.session.flush()
        except Exception:
            pass
        resp = Response({"ok": True})
        resp.delete_cookie("sessionid", path="/")
        resp.delete_cookie("csrftoken", path="/")
        resp.delete_cookie("refresh", path="/")
        resp.delete_cookie("dj_refresh", path="/")
        return resp
