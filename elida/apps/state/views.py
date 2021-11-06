from django.views.generic import TemplateView
from .models import State
from elida.apps.molecule.models import Molecule
from django_datatables_serverside.views import ServerSideDataTableView
from django.urls import reverse


class StateListView(TemplateView):
    template_name = 'state_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mol = Molecule.objects.get(slug=self.kwargs['mol_slug'])
        mol_html = mol.html
        context['mol_slug'] = self.kwargs['mol_slug']
        context['table_heading'] = f'States of {mol_html}'
        context['title'] = f'{mol.slug} states'
        context['resolves_el'] = mol.isotopologue.resolves_el()
        context['resolves_vib'] = mol.isotopologue.resolves_vib()
        return context


def number_transitions_from_value(instance):
    val = instance.number_transitions_from
    if not val:
        return ''
    href = reverse('transition-list-from-state', args=[instance.pk])
    cls = 'elida-link'
    return f'<a href="{href}" class="{cls}">{val}</a>'


def number_transitions_to_value(instance):
    val = instance.number_transitions_to
    if not val:
        return ''
    href = reverse('transition-list-to-state', args=[instance.pk])
    cls = 'elida-link'
    return f'<a href="{href}" class="{cls}">{val}</a>'


class StateDataTableView(ServerSideDataTableView):
    surrogate_columns_search = {'el_state_html': 'el_state_html_notags', 'vib_state_html': 'vib_state_html_notags'}
    surrogate_columns_sort = {'vib_state_html': 'vib_state_sort_key'}
    custom_value_getters = {
        'energy': lambda instance: f'{instance.energy:.3f}',
        'lifetime': lambda instance: f'{instance.lifetime:.2e}' if instance.lifetime is not None else '∞',
        'number_transitions_from': number_transitions_from_value,
        'number_transitions_to': number_transitions_to_value
    }

    @property
    def queryset(self):
        return State.objects.filter(isotopologue__molecule__slug=self.kwargs['mol_slug']).all()
