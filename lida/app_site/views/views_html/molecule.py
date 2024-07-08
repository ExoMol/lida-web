from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .utils import Column, Order


class MoleculeListView(TemplateView):
    template_name = "site/datatable.html"
    extra_context = {
        "title": "Species",
        "content_heading": "Species",
        "table_footer": True,
        "scroller": False,
        "ajax_url": reverse_lazy("molecule-list-ajax"),
        "datatable_id": "datatable-molecule",
        "initial_order": [Order(1), Order(2)],
        "columns": [
            Column("Species", "html", 0, searchable=True, individual_search=True),
            Column(
                "<em>N</em><sub>atoms</sub>",
                "number_atoms",
                1,
                searchable=True,
                individual_search=True,
                placeholder="N",
            ),
            Column("<em>m</em> (Da)", "isotopologue__mass", 2),
            Column("States", "isotopologue__number_states", 3),
            Column("Transitions", "isotopologue__number_transitions", 4),
        ],
    }
