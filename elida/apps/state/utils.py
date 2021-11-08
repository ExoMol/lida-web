from collections import namedtuple

from lxml import html
from pyvalem.state_parser import MolecularTermSymbol

from .exceptions import StateError


def validate_and_parse_vib_state_str(vib_state_str):
    """Helper function validating and parsing the vib_state_str.
    Returns list of quanta of the vibrational excitation, and the html representation. Raises StateError whenever the
    passed vib_state_str is not in exactly the correct format.
    """
    if vib_state_str == '':
        return [], ''

    invalid_state_str_msg = \
        f'Vibrational string "{vib_state_str}" is not in the form of "(v_1, v_2, ..., v_n)" or "v"!'

    if vib_state_str[0] == '(' and vib_state_str[-1] == ')':
        quanta_str = vib_state_str.lstrip('(').rstrip(')').split(', ')
        if len(quanta_str) < 2:
            raise StateError(invalid_state_str_msg)
    elif vib_state_str[0] != '(' and vib_state_str[-1] != ')':
        quanta_str = [vib_state_str, ]
    else:
        raise StateError(invalid_state_str_msg)

    try:
        quanta_int = [int(q) for q in quanta_str]
        vib_state_dim = len(quanta_int)
    except ValueError:
        raise StateError(invalid_state_str_msg)

    if [str(q) for q in quanta_int] != quanta_str:
        raise StateError(invalid_state_str_msg)

    if any(q < 0 for q in quanta_int):
        raise StateError(invalid_state_str_msg)

    if len(quanta_int) == 1:
        q = quanta_int[0]
        vib_state_html = f'<i>v</i>={q}'
    else:
        vib_state_html = f'<b><i>v</i></b>={vib_state_str}'

    return quanta_int, vib_state_html


def canonicalise_and_parse_el_state_str(el_state_str):
    """Helper function canonicalizing the el_state_str using the pyvalem package.
    Example:
        canonicalise_el_state_str('1SIGMA-')  = '1Σ-',
    """
    el_state_str = el_state_str.strip()
    if el_state_str == '':
        return '', ''
    canonicalised_el_state_str = repr(MolecularTermSymbol(el_state_str))
    el_state_html = get_el_state_html(el_state_str)
    return canonicalised_el_state_str, el_state_html


def get_el_state_html(el_state_str):
    el_state_str = el_state_str.strip()
    if el_state_str == '':
        return ''
    return MolecularTermSymbol(el_state_str).html


def get_state_str(isotopologue, el_state_str, vib_state_str):
    molecule_str = str(isotopologue.molecule)
    state_str = ';'.join(s for s in [el_state_str, f'v={vib_state_str.replace(" ", "")}'] if s)
    return f'{molecule_str} {state_str}'


def leading_zeros(vib_state_str):
    quanta_int, _ = validate_and_parse_vib_state_str(vib_state_str)
    return '(' + ', '.join(f'{q:02d}' for q in quanta_int) + ')'


def strip_tags(html_str):
    if html_str == '':
        return ''
    return html.fromstring(html_str).text_content()


Column = namedtuple('Column', 'heading model_field index visible searchable individual_search placeholder')
Order = namedtuple('Order', 'index dir')
