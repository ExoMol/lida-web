#from lxml import html
import re
from pyvalem.states import MolecularTermSymbol
from pyvalem.states import AtomicTermSymbol
from pyvalem.states import AtomicConfiguration
from pyvalem.states import RacahSymbol
from pyvalem.states import CompoundLSCoupling
from pyvalem.states.J1K_LK_coupling import J1K_LK_Coupling
from pyvalem.states.J1K_LK_coupling import J1K_LK_CouplingError

from django.db import models

from .exceptions import StateError


class BaseModel(models.Model):
    """Abstract base class for all the models implemented in the models sub-package."""

    id = models.AutoField(primary_key=True)
    time_added = models.DateTimeField(auto_now_add=True)
    time_modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    # abstract attributes:
    sync_functions = {}

    def str_to_repr(self, text):
        # noinspection PyUnresolvedReferences
        return f"{self.id}:{self._meta.object_name}({text})"

    def __repr__(self):
        return self.str_to_repr(str(self))

    @property
    def model_name(self):
        return self._meta.model.__name__

    def sync(self, verbose=False, sync_only=None, skip=None, save=True):
        """Method to sync the instance with all the other related database models.
        All the fields which are not explicit inputs to the create_from_data method
        depend on other models related to this instance and can be synced by this method
        whenever the related models get changed.
        This is a way around this database model being very poorly normalized
        (in favor of performance).
        WARNING: must call .save on the child class instance to commit the changes into
        database!
        """
        if sync_only is None and skip is None:
            attributes_to_sync = list(self.sync_functions)
        elif sync_only is not None:
            attributes_to_sync = sync_only
        elif skip is not None:
            attributes_to_sync = [
                attr for attr in self.sync_functions if attr not in skip
            ]
        else:
            raise ValueError('Only one attribute of "sync_only", "skip" may be passed!')

        update_log = []

        for attr_name in attributes_to_sync:
            val_synced = self.sync_functions[attr_name](self)
            val_orig = getattr(self, attr_name)
            if val_synced != val_orig:
                setattr(self, attr_name, val_synced)
                update_log.append(f"updated {attr_name}: {val_orig} -> {val_synced}")

        if verbose and len(update_log):
            object_repr = repr(self)
            entry = update_log.pop(0)
            print(f"{object_repr}: {entry}")
            for entry in update_log:
                print(f'{len(object_repr) * " "}  {entry}')

        if save:
            self.save()


def validate_and_parse_vib_state_str(vib_state_str):
    """Helper function validating and parsing the vib_state_str.
    Returns list of quanta of the vibrational excitation, and the html representation.
    Raises StateError whenever the passed vib_state_str is not in exactly the correct
    format.
    """
    if vib_state_str == "":
        return [], ""
    #ALEC
    # Check if vib_state_str contains s,p,d,f,g,h, then use pyvalem atomic configuration format
    valid_shells = ["s", "p", "d", "f", "g", "h"]
    vib_state_str = vib_state_str.strip()

    #ALEC
    # Check if the vib_state_str has the form e.g."1s2.2s2(3P).3s"
    if len(vib_state_str) >= 2 and vib_state_str[1] in valid_shells and "(" in vib_state_str and ")" in vib_state_str:
        vib_state_html = CompoundLSCoupling(vib_state_str).html
        quanta_int = [1]
        return quanta_int, vib_state_html
    # If not check is atomic configuration format e.g. "1s2.2s2.2p6"
    if len(vib_state_str) >= 2 and vib_state_str[1] in valid_shells:
        vib_state_html = AtomicConfiguration(vib_state_str).html
        quanta_int = [1]
        return quanta_int, vib_state_html
    #ALEC

    invalid_state_str_msg = (
        f'Vibrational string "{vib_state_str}" is not in the form of '
        f'"(v_1, v_2, ..., v_n)" or "v"!'
    )

    if vib_state_str[0] == "(" and vib_state_str[-1] == ")":
        quanta_str = vib_state_str.lstrip("(").rstrip(")").split(", ")
        if len(quanta_str) < 2:
            raise StateError(invalid_state_str_msg)
    elif vib_state_str[0] != "(" and vib_state_str[-1] != ")":
        quanta_str = [
            vib_state_str,
        ]
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
        vib_state_html = f"<i>v</i>={q}"
    else:
        vib_state_html = f"<b><i>v</i></b>={vib_state_str}"

    return quanta_int, vib_state_html


def canonicalise_and_parse_el_state_str(el_state_str):
    """Helper function canonicalizing the el_state_str using the pyvalem package.
    Example:
        canonicalise_el_state_str('1SIGMA-')  = '1Σ-',
    """
    el_state_str = el_state_str.strip()
    if el_state_str == "":
        return "", ""
    #ALEC
    # Handling for the special case using J1K_LK_Coupling or RacahSymbol
    if "[" in el_state_str and "]" in el_state_str:
        # Check if it matches J1K_LK_Coupling pattern like "2[4]" or "2[3/2]o"
        try:
            canonicalised_el_state_str = repr(J1K_LK_Coupling(el_state_str))
            el_state_html = get_el_state_html(el_state_str)
            return canonicalised_el_state_str, el_state_html
        except J1K_LK_CouplingError:
            # If J1K_LK_Coupling parsing fails, try RacahSymbol
            canonicalised_el_state_str = repr(RacahSymbol(el_state_str))
            el_state_html = get_el_state_html(el_state_str)
            return canonicalised_el_state_str, el_state_html
    #Check if the first character of el_state_str is a digit to indicate atomic term notation
    if el_state_str[0].isdigit() or (len(el_state_str) > 1 and el_state_str[1].isdigit()):
        canonicalised_el_state_str = repr(AtomicTermSymbol(el_state_str))
        el_state_html = get_el_state_html(el_state_str)
        return canonicalised_el_state_str, el_state_html
    #ALEC
    canonicalised_el_state_str = repr(MolecularTermSymbol(el_state_str))
    el_state_html = get_el_state_html(el_state_str)
    return canonicalised_el_state_str, el_state_html    


def get_el_state_html(el_state_str):
    el_state_str = el_state_str.strip()
    if el_state_str == "":
        return ""
    #ALEC
    # Check if the el_state_str has J1K_LK_Coupling Racah Symbol form, e.g. 2[3/2]
    if "[" in el_state_str and "]" in el_state_str:
        try:
            # Attempt to parse as J1K_LK_Coupling
            return J1K_LK_Coupling(el_state_str).html
        except J1K_LK_CouplingError:
            # If parsing as J1K_LK_Coupling fails, attempt to parse as RacahSymbol
            return RacahSymbol(el_state_str).html
    #Check if the first character of el_state_str is a digit to indicate atomic term notation
    if el_state_str[0].isdigit() or (len(el_state_str) > 1 and el_state_str[1].isdigit()):
        return AtomicTermSymbol(el_state_str).html
    #ALEC
    return MolecularTermSymbol(el_state_str).html

def get_state_str(isotopologue, el_state_str, vib_state_str):
    molecule_str = str(isotopologue.molecule)
    state_str = ";".join(
        s for s in [el_state_str, f'v={vib_state_str.replace(" ", "")}'] if s
    )
    return f"{molecule_str} {state_str}"


def leading_zeros(vib_state_str):
    quanta_int, _ = validate_and_parse_vib_state_str(vib_state_str)
    return "(" + ", ".join(f"{q:02d}" for q in quanta_int) + ")"


def strip_tags(html_str):
    if html_str == "":
        return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', html_str)
    #return html.fromstring(html_str).text_content()
