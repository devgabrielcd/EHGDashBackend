from typing import Optional, Tuple
import re
from django.contrib.auth.models import User
from django.utils.text import slugify

from src.users.models import Profile, UserType
from src.company.models import Company

def _normalize_phone(v: Optional[str]) -> str:
    return re.sub(r"\D", "", v or "")

def _unique_username(base: str) -> str:
    base = re.sub(r"[^a-z0-9._-]+", "", slugify(base or "user", allow_unicode=False))
    if not User.objects.filter(username=base).exists():
        return base
    i = 2
    while True:
        cand = f"{base}{i}"
        if not User.objects.filter(username=cand).exists():
            return cand
        i += 1

def _derive_username(email: str, first_name: str, last_name: str, phone_norm: str) -> str:
    if email and "@" in email:
        return _unique_username(email.split("@", 1)[0])
    if first_name or last_name:
        return _unique_username(f"{first_name}.{last_name}".replace("..","."))
    if phone_norm:
        return _unique_username(f"user{phone_norm[-6:]}")
    return _unique_username("user")

def get_or_create_customer_usertype() -> UserType:
    ut = UserType.objects.filter(user_type__iexact="Customer").first()
    if not ut:
        ut = UserType.objects.create(user_type="Customer")
    return ut

def find_profile_by_contact(email: Optional[str], phone_norm: Optional[str]) -> Optional[Profile]:
    email = (email or "").strip().lower()
    phone_norm = _normalize_phone(phone_norm)
    if email:
        prof = Profile.objects.filter(email__iexact=email).select_related("user").first()
        if prof:
            return prof
        user = User.objects.filter(email__iexact=email).first()
        if user and hasattr(user, "profile"):
            return user.profile
    if phone_norm:
        prof = Profile.objects.filter(phone_number=phone_norm).select_related("user").first()
        if prof:
            return prof
    return None

def create_or_update_user_profile_from_form(
    *,
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    company: Optional[Company],
    coverageType: Optional[str],
    insuranceCoverage: Optional[str],
    formType: Optional[str],
) -> Tuple[User, Profile]:
    """
    Sem signals. Garante User+Profile e user_type=Customer.
    Atualiza campos sem apagar os existentes úteis.
    """
    email = (email or "").strip().lower()
    phone_norm = _normalize_phone(phone)

    prof = find_profile_by_contact(email, phone_norm)

    if not prof:
        username = _derive_username(email, first_name, last_name, phone_norm)
        user = User.objects.create_user(username=username, email=email or None, password=None)
        user.set_unusable_password()
        if first_name and not user.first_name:
            user.first_name = first_name
        if last_name and not user.last_name:
            user.last_name = last_name
        user.save()
        prof = Profile.objects.create(user=user)
    else:
        user = prof.user
        # Atualiza o User de forma não destrutiva
        if email and not user.email:
            user.email = email
        if first_name and not user.first_name:
            user.first_name = first_name
        if last_name and not user.last_name:
            user.last_name = last_name
        user.save()

    # user_type = Customer
    customer_ut = get_or_create_customer_usertype()
    if not prof.user_type_id or prof.user_type_id != customer_ut.id:
        prof.user_type = customer_ut

    # Campos do Profile (não destrutivo no que for pessoal)
    if first_name and not prof.first_name:
        prof.first_name = first_name
    if last_name and not prof.last_name:
        prof.last_name = last_name
    if email and not prof.email:
        prof.email = email
    if phone_norm and not prof.phone_number:
        prof.phone_number = phone_norm
    if company and not prof.company_id:
        prof.company = company

    # Estes podem refletir o último interesse
    if coverageType:
        prof.coverageType = coverageType
    if insuranceCoverage:
        prof.insuranceCoverage = insuranceCoverage
    if formType:
        prof.formType = formType

    prof.save()
    return user, prof
