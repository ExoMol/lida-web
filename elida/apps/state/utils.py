from pyvalem.state_parser import MolecularTermSymbol, VibrationalState

from .exceptions import StateError


def validate_and_parse_vib_state_str(vib_state_str):
    """Helper function validating and parsing the vib_state_str.
    Returns dimensionality of the vibrational excitation, and two html representations. Raises StateError whenever the
    passed vib_state_str is not in exactly the correct format.
    """
    if vib_state_str == '':
        return 0, '', ''

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
        vib_state_html = vib_state_html_alt = f'<i>v</i>={q}'
    elif not any(quanta_int):
        vib_state_html = vib_state_html_alt = f'<b><i>v</i></b>=<b>0</b>'
    else:
        pyvalem_str = '+'.join(f'{q}v{v}' for v, q in enumerate(quanta_int, start=1) if q > 0)
        vib_state_html = VibrationalState(pyvalem_str).html
        vib_state_html_alt = f'<b><i>v</i></b>={vib_state_str}'

    return vib_state_dim, vib_state_html, vib_state_html_alt


def canonicalise_and_parse_el_state_str(el_state_str):
    """Helper function canonicalizing the el_state_str using the pyvalem package.
    Example:
        canonicalise_el_state_str('1SIGMA-')  = '1Σ-',
    """
    el_state_str = el_state_str.strip()
    if el_state_str == '':
        return '', ''
    el_state = MolecularTermSymbol(el_state_str)
    canonicalised_el_state_str = repr(el_state)
    el_state_html = el_state.html
    return canonicalised_el_state_str, el_state_html


def get_state_str(isotopologue, el_state_str, vib_state_str):
    molecule_str = str(isotopologue.molecule)
    state_str = ';'.join(s for s in [el_state_str, f'v={vib_state_str.replace(" ", "")}'] if s)
    return f'{molecule_str} {state_str}'
