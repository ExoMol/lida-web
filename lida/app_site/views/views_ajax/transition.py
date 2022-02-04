from django_datatables_serverside.views import ServerSideDataTableView

from app_site.models import Molecule, State


class _Base(ServerSideDataTableView):
    surrogate_columns_search = {
        "initial_state__state_html": "initial_state__state_html_notags",
        "final_state__state_html": "final_state__state_html_notags",
    }
    surrogate_columns_sort = {
        "initial_state__state_html": "initial_state__state_sort_key",
        "final_state__state_html": "final_state__state_sort_key",
    }
    custom_value_getters = {
        "delta_energy": lambda tr: f"{tr.delta_energy:.3f}",
        "partial_lifetime": lambda tr: f"{tr.partial_lifetime:.2e}"
        if tr.partial_lifetime is not None
        else "∞",
    }
    queryset = None


class TransitionToStateListAjaxView(_Base):
    @property
    def queryset(self):
        return State.objects.get(pk=self.kwargs["state_pk"]).transition_to_set.all()


class TransitionFromStateListAjaxView(_Base):
    @property
    def queryset(self):
        return State.objects.get(pk=self.kwargs["state_pk"]).transition_from_set.all()


class TransitionListAjaxView(_Base):
    @property
    def queryset(self):
        return Molecule.objects.get(
            slug=self.kwargs["mol_slug"]
        ).isotopologue.transition_set.all()
