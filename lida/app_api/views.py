import io
import csv
from django.utils.datastructures import MultiValueDictKeyError
from django.views.generic import TemplateView
from django.http import JsonResponse, Http404, HttpResponse
#from django.core import serializers

from app_site.models.molecule import Molecule
from app_site.models.transition import Transition

class ApiAboutView(TemplateView):
    template_name = "api/about.html"
    extra_context = {"title": "API", "content_heading": "About the public API"}



def get_state_lifetimes_dict(isotopologue, states):
    return dict([(str(state), {'lifetime': state.lifetime,
                               'energy': state.energy}) for state in states])
 
def get_transition_lifetimes_dict(isotopologue, transitions):
    return dict([(str(transition), {'partial_lifetime': transition.partial_lifetime,
                                    'delta_energy': transition.delta_energy})
                 for transition in transitions])
 
def get_state_lifetimes_csv(isotopologue, states):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["State", "Lifetime /s", "Energy /eV"])
    for state in states:
        csv_row_data = [str(state), state.lifetime, state.energy]
        writer.writerow(csv_row_data)
    return output.getvalue()

def get_transitions_lifetimes_csv(isotopologue, transitions):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Initial State", "Final State", "Partial Lifetime /s",
                     "Delta Energy /eV"])
    for transition in transitions:
        csv_row_data = [transition.initial_state, transition.initial_state,
                        transition.partial_lifetime, transition.delta_energy]
        writer.writerow(csv_row_data)
    return output.getvalue()

def api_endpoint(request):
    try:
        molecule = request.GET.get('molecule')
        category = request.GET['category'].lower()
    except MultiValueDictKeyError:
        json_response = {'msg': 'API query must include molecule and category'}
        return JsonResponse(json_response)
    if category not in ('states', 'transitions'):
        json_response = {'msg': 'category must be one of states or transitions'}
        return JsonResponse(json_response)

    try:
        molecule = Molecule.objects.get(formula_str=molecule)
    except Molecule.DoesNotExist:
        raise Http404
    isotopologue = molecule.isotopologue

    fmt = request.GET.get('format', 'json').lower()

    if fmt not in ('json', 'csv'):
        json_response = {'msg': f"{fmt} is not a supported output format; format"
                                f" must be one of 'json' or 'csv'."}
        return JsonResponse(json_response)

    if category == 'states':
        states = isotopologue.state_set.all()
    else:
        transitions = Transition.objects.filter(initial_state__isotopologue=isotopologue)

    if fmt == 'csv':
        if category == 'states':
            return HttpResponse(get_state_lifetimes_csv(isotopologue, states),
                                content_type='text/csv')
        else:
            return HttpResponse(get_transitions_lifetimes_csv(isotopologue,
                                transitions),
                                content_type='text/csv')

    #molecule = serializers.serialize('json', [molecule,])
    molecule_formula = molecule.formula_str
    isotopologue_formula = isotopologue.iso_formula_str
    dataset_name = isotopologue.dataset_name
    version = isotopologue.version
    number_states = isotopologue.number_states
    number_transitions = isotopologue.number_transitions
    molecule_dict = {'molecule_formula': molecule_formula,
                     'isotopologue_formula': isotopologue_formula,
                    }
    dataset_dict = {'name': dataset_name,
                    'version': version,
                    'number_states': number_states,
                    'number_transitions': number_transitions
                   }

    json_response = {'molecule': molecule_dict, 'dataset': dataset_dict}

    if category == 'states':
        json_response['states'] = get_state_lifetimes_dict(isotopologue, states)
    else:
        json_response['transitions'] = get_transition_lifetimes_dict(
                                                    isotopologue, transitions)

    return JsonResponse(json_response)


