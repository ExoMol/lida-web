from django.urls import reverse
from django_datatables_serverside.views import ServerSideDataTableView

from app_site.models import State


def number_transitions_from_value(instance):
    val = instance.number_transitions_from
    if not val:
        return ""
    href = reverse("transition-from-state-list", args=[instance.pk])
    cls = "site-link"
    return f'<a href="{href}" class="{cls}">{val}</a>'


def number_transitions_to_value(instance):
    val = instance.number_transitions_to
    if not val:
        return ""
    href = reverse("transition-to-state-list", args=[instance.pk])
    cls = "site-link"
    return f'<a href="{href}" class="{cls}">{val}</a>'


class StateListAjaxView(ServerSideDataTableView):
    surrogate_columns_search = {
        "el_state_html": "el_state_html_notags",
    }
    surrogate_columns_sort = {"vib_state_str": "vib_state_sort_key"}
    custom_value_getters = {
        "energy": lambda instance: f"{instance.energy:.3f}",
        "lifetime": lambda instance: f"{instance.lifetime:.2e}"
        if instance.lifetime is not None
        else "∞",
        "number_transitions_from": number_transitions_from_value,
        "number_transitions_to": number_transitions_to_value,
    }

    @property
    def queryset(self):
        return State.objects.filter(
            isotopologue__molecule__slug=self.kwargs["mol_slug"]
        ).all()
