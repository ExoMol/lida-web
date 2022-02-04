from django.urls import reverse
from django.views.generic import TemplateView

from app_site.models import Molecule, State
from .utils import Column, Order


class _Base(TemplateView):
    template_name = "site/datatable.html"
    extra_context = {
        "table_footer": True,
        "initial_order": [Order(0), Order(1)],
        "columns": [
            Column(
                "Initial state",
                "initial_state__state_html",
                0,
                searchable=True,
                individual_search=True,
            ),
            Column(
                "Final state",
                "final_state__state_html",
                1,
                searchable=True,
                individual_search=True,
            ),
            Column("Δ<em>E</em> (eV)", "delta_energy", 2),
            Column("Partial lifetime (s)", "partial_lifetime", 3),
        ],
        "scroller": True,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state, self.molecule = None, None

    def get_context_data(self, **kwargs):
        self.save_state_and_molecule()
        context = super().get_context_data(**kwargs)
        context["title"] = f"{self.molecule.slug} transitions"
        context["search_footer"] = True
        context["length_change"] = True
        # to be implemented in the child classes:
        context["content_heading"] = None
        context["ajax_url"] = None
        return context

    def save_state_and_molecule(self):
        if "mol_slug" in self.kwargs:
            self.state = None
            self.molecule = Molecule.objects.get(slug=self.kwargs["mol_slug"])
        elif "state_pk" in self.kwargs:
            self.state = State.objects.get(pk=self.kwargs["state_pk"])
            self.molecule = self.state.isotopologue.molecule
        else:
            raise ValueError(
                "If this happens, make sure that mol_slug or state_pk are passed to "
                "views from urls"
            )


class TransitionToStateListView(_Base):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[
            "content_heading"
        ] = f"Transitions of {self.molecule.html} to the state {self.state.state_html}"
        context["ajax_url"] = reverse(
            "transition-to-state-list-ajax", args=[self.state.pk]
        )
        context["datatable_id"] = f"datatable-transition-to-state-{self.state.pk}"
        return context


class TransitionFromStateListView(_Base):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["content_heading"] = (
            f"Transitions of {self.molecule.html} from the state "
            f"{self.state.state_html}"
        )
        context["ajax_url"] = reverse(
            "transition-from-state-list-ajax", args=[self.state.pk]
        )
        context["datatable_id"] = f"datatable-transition-from-state-{self.state.pk}"
        return context


class TransitionListView(_Base):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["content_heading"] = f"Transitions of {self.molecule.html}"
        context["ajax_url"] = reverse("transition-list-ajax", args=[self.molecule.slug])
        context["datatable_id"] = f"datatable-transition-{self.molecule.slug}"
        return context
