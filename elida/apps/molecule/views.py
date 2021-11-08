from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView
from django_datatables_serverside.views import ServerSideDataTableView

from elida.apps.state.utils import Column, Order
from .models import Molecule


class MoleculeListView(TemplateView):
    template_name = 'datatable.html'
    extra_context = {
        'title': 'Molecules',
        'content_heading': 'Molecules',
        'search_footer': True,
        'length_change': True,
        'ajax_url': reverse_lazy('molecule-all-ajax'),
        'initial_order': [Order(1, 'asc'), Order(2, 'asc')],
        'columns': [
            Column('Molecule', 'html', 0, True, True, True, ''),
            Column('<em>N</em><sub>atoms</sub>', 'number_atoms', 1, True, True, True, 'N'),
            Column('<em>m</em> (amu)', 'isotopologue__mass', 2, True, False, False, ''),
            Column('States', 'isotopologue__number_states', 3, True, False, False, ''),
            Column('Transitions', 'isotopologue__number_transitions', 4, True, False, False, ''),
        ]
    }


def molecule_details_html(molecule):
    states_href = reverse('state-list', args=[molecule.slug])
    transitions_href = reverse('transition-list-mol_slug', args=[molecule.slug])
    anchor_style = 'elida-link'
    mol_details_html = f'''
    <a href="#" class="{anchor_style}" data-bs-toggle="modal" data-bs-target="#molecule-details-{molecule.pk}">{molecule.html}</a>
    <div class="modal fade" role="dialog" id="molecule-details-{molecule.pk}" tabindex="-1" aria-hidden="true" aria-labelledby="MoleculeDetails{molecule.pk}">
    <div class="modal-dialog">
      <div class="modal-content bg-dark modal-details">
        <div class="modal-header">
          <h5 class="modal-title">Molecule details</h5>
        </div>
        <div class="modal-body">
          <div class="row">
            <div class="col-7">Formula:</div>
            <div class="col-5">{molecule.html}</div>
          </div>
          <div class="row">
            <div class="col-7">Name:</div>
            <div class="col-5">{molecule.name}</div>
          </div>
          <div class="row">
            <div class="col-7">Isotopologue:</div>
            <div class="col-5">{molecule.isotopologue.html}</div>
          </div>
          <div class="row">
            <div class="col-7">Resolves electronic states:</div>
            <div class="col-5">{"Yes" if molecule.isotopologue.resolves_el else "No"}</div>
          </div>
          <div class="row{" hidden-element" if not molecule.isotopologue.resolves_el else ""}">
            <div class="col-7">Electronic ground state:</div>
            <div class="col-5">{molecule.isotopologue.ground_el_state_html}</div>
          </div>
          <div class="row">
            <div class="col-7">Resolves vibrational states:</div>
            <div class="col-5">{"Yes" if molecule.isotopologue.resolves_vib else "No"}</div>
          </div>
          <div class="row{" hidden-element" if not molecule.isotopologue.resolves_vib else ""}">
            <div class="col-7">Vibrational quantum numbers:</div>
            <div class="col-5">{molecule.isotopologue.vib_quantum_numbers_html}</div>
          </div>
          <div class="row">
            <div class="col-7">Mass (amu):</div>
            <div class="col-5">{molecule.isotopologue.mass:.5f}</div>
          </div>
          <div class="row">
            <div class="col-7">States:</div>
            <div class="col-5">
              <a href="{states_href}" class="{anchor_style}">{molecule.isotopologue.number_states}</a>
            </div>
          </div>
          <div class="row">
            <div class="col-7">Transitions:</div>
            <div class="col-5">
              <a href="{transitions_href}" class="{anchor_style}">{molecule.isotopologue.number_transitions}</a>
            </div>
          </div>
          <div class="row">
            <div class="col-7">Exomol dataset name:</div>
            <div class="col-5">
              <a href="https://www.exomol.com/data/molecules/{molecule.slug}/{molecule.isotopologue.iso_slug}/{molecule.isotopologue.dataset_name}" class="{anchor_style}" target="_blank" rel="noopener noreferrer">{molecule.isotopologue.dataset_name}</a>
            </div>
          </div>
        </div>
      </div>
    </div>
    </div>
    '''
    return mol_details_html


def number_states_value(molecule):
    val = molecule.isotopologue.number_states
    href = reverse('state-list', args=[molecule.slug])
    cls = 'elida-link'
    return f'<a href="{href}" class="{cls}">{val}</a>'


def number_transitions_value(molecule):
    val = molecule.isotopologue.number_transitions
    href = reverse('transition-list-mol_slug', args=[molecule.slug])
    cls = 'elida-link'
    return f'<a href="{href}" class="{cls}">{val}</a>'


class MoleculeDataTableAjaxView(ServerSideDataTableView):
    custom_value_getters = {
        'html': molecule_details_html,
        'isotopologue__mass': lambda mol: f'{mol.isotopologue.mass:.2f}',
        'isotopologue__number_states': number_states_value,
        'isotopologue__number_transitions': number_transitions_value
    }
    surrogate_columns_search = {'html': 'formula_str'}
    queryset = Molecule.objects.all()
