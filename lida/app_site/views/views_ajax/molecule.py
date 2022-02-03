from django.template.loader import render_to_string
from django.urls import reverse
from django_datatables_serverside.views import ServerSideDataTableView

from app_site.models import Molecule


def molecule_details_html(molecule):
    return render_to_string(
        "site/molecule_details.html", context={"molecule": molecule}
    )


def number_states_value(molecule):
    val = molecule.isotopologue.number_states
    href = reverse("state-list", args=[molecule.slug])
    cls = "site-link"
    return f'<a href="{href}" class="{cls}">{val}</a>'


def number_transitions_value(molecule):
    val = molecule.isotopologue.number_transitions
    href = reverse("transition-list", args=[molecule.slug])
    cls = "site-link"
    return f'<a href="{href}" class="{cls}">{val}</a>'


class MoleculeListAjaxView(ServerSideDataTableView):
    custom_value_getters = {
        "html": molecule_details_html,
        "isotopologue__mass": lambda mol: f"{mol.isotopologue.mass:.2f}",
        "isotopologue__number_states": number_states_value,
        "isotopologue__number_transitions": number_transitions_value,
    }
    surrogate_columns_search = {"html": "formula_str"}
    queryset = Molecule.objects.all()
