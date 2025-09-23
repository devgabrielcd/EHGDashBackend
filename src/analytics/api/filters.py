# src/analytics/api/filters.py
import django_filters
from django_filters import rest_framework as filters
from django.contrib.auth import get_user_model

from src.users.models import Profile
from src.forms.models import FormSubmission  # ⬅️ novo

User = get_user_model()


# Helper "IN" filter para strings: ?insuranceCoverage__in=Health,Dental
class CharInFilter(django_filters.BaseInFilter, django_filters.CharFilter):
    pass


class ProfileFilterSet(filters.FilterSet):
    """
    Filtros para agregações baseadas em Profile.
    Exemplos de uso:
      ?company=2
      ?insuranceCoverage=Health
      ?insuranceCoverage__in=Health,Dental
      ?coverageType=family
      ?include_unknown=1
    """
    company = filters.NumberFilter(field_name="company__id")
    insuranceCoverage = filters.CharFilter(field_name="insuranceCoverage", lookup_expr="iexact")
    insuranceCoverage__in = CharInFilter(field_name="insuranceCoverage", lookup_expr="in")
    coverageType = filters.CharFilter(field_name="coverageType", lookup_expr="iexact")
    include_unknown = filters.BooleanFilter(method="filter_include_unknown")

    def filter_include_unknown(self, queryset, name, value):
        # Por padrão, exclui NULL/""; se include_unknown=1, mantém
        if value:
            return queryset
        return (queryset
                .exclude(insuranceCoverage__isnull=True).exclude(insuranceCoverage__exact="")
                .exclude(coverageType__isnull=True).exclude(coverageType__exact=""))

    class Meta:
        model = Profile
        fields = ["company", "insuranceCoverage", "coverageType"]


class UserFilterSet(filters.FilterSet):
    """
    Filtros para User (com dados do Profile via select_related).
    Exemplos:
      ?company=2
      ?date_joined_after=2025-01-01
      ?date_joined_before=2025-12-31
      ?q=gabriel        (username/email icontains)
    """
    company = filters.NumberFilter(field_name="profile__company__id")
    date_joined_after = filters.DateFilter(field_name="date_joined", lookup_expr="date__gte")
    date_joined_before = filters.DateFilter(field_name="date_joined", lookup_expr="date__lte")
    q = filters.CharFilter(method="filter_q")

    def filter_q(self, queryset, name, value):
        from django.db.models import Q
        v = (value or "").strip()
        if not v:
            return queryset
        return queryset.filter(Q(username__icontains=v) | Q(email__icontains=v))

    class Meta:
        model = User
        fields = ["company"]


# ⬇️ NOVO: filtros para envios de formulário
class FormSubmissionFilterSet(filters.FilterSet):
    """
    Filtros para FormSubmission (novo app forms).
    Exemplos:
      ?company=2
      ?formType=Homepage%20Form
      ?formType__in=Homepage%20Form,Appointment%20Form
      ?created_after=2025-01-01
      ?created_before=2025-12-31
    """
    company = filters.NumberFilter(field_name="company__id")
    formType = filters.CharFilter(field_name="formType", lookup_expr="iexact")
    formType__in = CharInFilter(field_name="formType", lookup_expr="in")
    created_after = filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    created_before = filters.DateFilter(field_name="created_at", lookup_expr="date__lte")

    class Meta:
        model = FormSubmission
        fields = ["company", "formType"]
