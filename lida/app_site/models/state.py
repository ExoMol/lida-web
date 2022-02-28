from collections import OrderedDict

from django.db import models

from .exceptions import StateError
from .isotopologue import Isotopologue
from .utils import (
    validate_and_parse_vib_state_str,
    canonicalise_and_parse_el_state_str,
    get_state_str,
    leading_zeros,
    strip_tags,
    BaseModel,
)


class State(BaseModel):
    # noinspection PyUnresolvedReferences
    """A data model representing a stateful species. The stateless species is
    represented by the Isotopologue instance and its state is created by
    pyvalem.state compatible strings.
    Only a single State instance belonging to the same Isotopologue and describing
    the same physical state should exist at any given time in the database.
    To ensure this, it is recommended to use available class methods for creating
    new instances.

    Attributes
    ----------
    el_state_str : str
        Example: 'X(1Σ+)'
    el_state_html : str
        Example: 'X<sup>1</sup>Σ<sup>+</sup>'
    el_state_html_notags : str
        Example: 'X1Σ+'
        For filtering through the html fields.
    vib_state_str : str
        Example: '1'
    vib_state_html : str
        Example: '<i>v</i>=1'
    vib_state_html_notags : str
        Example: 'v=0'
    state_sort_key : str
        Example: '(00)'

    Attribute Examples
    ------------------
                            | example 1                     | example 2
    ------------------------|-------------------------------|-----------
    el_state_str            | 'a(3Π)'                       | ''
    el_state_html           | 'a<sup>3</sup>Π'              | ''
    el_state_html_notags    | 'a3Π'                         | ''
    vib_state_str           | '1'                           | '(0, 3, 0)'
    vib_state_html          | '<i>v</i>=1'                  | '<b><i>v</i></b>=(0, 3, 0)'
    vib_state_html_notags   | 'v=1'                         | 'v=(0, 3, 0)'
    vib_state_sort_key      | '(01)'                        | '(00, 03, 00)'
    state_html              | 'a<sup>3</sup>Π; <i>v</i>=1'  | '<b><i>v</i></b>=(0, 3, 0)'
    state_html_notags       | 'a3Π; v=1'                    | 'v=(0, 3, 0)'
    state_sort_key          | 'a(3Π); (01)'                 | '(00, 03, 00)'
    """
    isotopologue = models.ForeignKey(Isotopologue, on_delete=models.CASCADE)

    # null fields denoting float('inf') which are not supported in MySQL
    lifetime = models.FloatField(null=True)
    energy = models.FloatField()

    # el_state_str is compatible with pyvalem MolecularTermSymbol (what repr of the
    # pyvalem class returns), e.g. '1Σ-'
    el_state_str = models.CharField(max_length=64)
    # vib_state_str is always a string and denoting either a vector or a single v,
    # e.g. '(0, 1, 0, 3)', '(0, 0, 0, 0)', and '5'
    vib_state_str = models.CharField(max_length=64)

    # the sync functions dict needs to be ordered, as the html attribute sync function
    # expects el_state_html and vib_state_html already synced
    sync_functions = OrderedDict(
        [
            (
                "el_state_str",
                lambda state: canonicalise_and_parse_el_state_str(state.el_state_str)[
                    0
                ],
            ),
            (
                "el_state_html",
                lambda state: canonicalise_and_parse_el_state_str(state.el_state_str)[
                    1
                ],
            ),
            ("el_state_html_notags", lambda state: strip_tags(state.el_state_html)),
            (
                "vib_state_html",
                lambda state: validate_and_parse_vib_state_str(state.vib_state_str)[1],
            ),
            ("vib_state_html_notags", lambda state: strip_tags(state.vib_state_html)),
            ("vib_state_sort_key", lambda state: leading_zeros(state.vib_state_str)),
            (
                "state_html",
                lambda state: "; ".join(
                    s for s in [state.el_state_html, state.vib_state_html] if s
                ),
            ),
            ("state_html_notags", lambda state: strip_tags(state.state_html)),
            (
                "state_sort_key",
                lambda state: "; ".join(
                    s for s in [state.el_state_str, state.vib_state_sort_key] if s
                ),
            ),
            (
                "number_transitions_from",
                lambda state: state.transition_from_set.count(),
            ),
            ("number_transitions_to", lambda state: state.transition_to_set.count()),
        ]
    )

    # following fields are auto-added when using the dedicated create_from methods
    # (or the sync method).
    el_state_html = models.CharField(max_length=64)
    el_state_html_notags = models.CharField(max_length=64)
    vib_state_html = models.CharField(max_length=64)
    vib_state_html_notags = models.CharField(max_length=64)
    vib_state_sort_key = models.CharField(max_length=64)
    state_html = models.CharField(max_length=128)
    state_html_notags = models.CharField(max_length=128)
    state_sort_key = models.CharField(max_length=128)
    # The following fields describe the meta-data about the transitions assigned to the
    # state, handled automatically when using the dedicated create_from methods...
    # auto-inc/dec on transition creation/deletion:
    number_transitions_from = models.PositiveIntegerField()
    number_transitions_to = models.PositiveIntegerField()

    def __str__(self):
        return get_state_str(self.isotopologue, self.el_state_str, self.vib_state_str)

    @classmethod
    def get_from_data(cls, isotopologue, el_state_str="", vib_state_str=""):
        """Example:
            isotopologue = Isotopologue.get_from_iso_formula_str('(12C)(16O)'),
            el_state_str = '1SIGMA-',
            vib_state_str = '(42, 0, 0)',
        The el_state_str gets canonicalised using pyvalem package (where the __repr__
        method on objects is meant to return a canonicalized representation of the
        given object).
        Only one instance for the given pair of arguments should exist in the database
        at any given time, otherwise it might lead to some inconsistent behaviour.
        """
        canonicalised_el_state_str, _ = canonicalise_and_parse_el_state_str(
            el_state_str
        )
        return cls.objects.get(
            isotopologue=isotopologue,
            el_state_str=canonicalised_el_state_str,
            vib_state_str=vib_state_str,
        )

    @classmethod
    def create_from_data(
        cls,
        isotopologue,
        lifetime,
        energy,
        el_state_str="",
        vib_state_labels="",
        vib_state_str="",
    ):
        """Example:
            isotopologue = Isotopologue.get_from_iso_formula_str('(12C)(16O)'),
            el_state_str = '1SIGMA-',
            vib_state_labels = '(v1, v2lin, v3)',
            vib_state_str = '(1, 0, 0)',
            lifetime = 0.42e-42,
            energy = 0.42

        The state_str gets canonicalized, so the saved state_str might differ from the
        passed state_str. However, the State.get_from_data will also reflect the
        canonicalization, so if both methods are used, it is irrelevant what state_str
        strings were used to save the state into the database.

        The el_state_str needs to be compatible with
        pyvalem.states.MolecularTermSymbol class.

        The vib_state_str needs to be one of two options:
            'v', where v is a positive integer (e.g. '0', '2', ...)
            '(v1, v2, v3, ...v_n)', where v1-n are positive integers.
                E.g. '(0, 0, 0)', '(1, 2, 3, 5, 0)', ..., where the vector dimension is
                greater than 1.

        If the el_state_str is passed, the parent isotopologue needs to also have
        non-empty ground_el_state_str, which should match whatever el_state_str are
        present in the State instances representing electronic ground states.
        E.g., before creating states for SiH, which resolve 4 distinct electronic
        states {'A(2DELTA)', 'B(2SIGMA+)', 'X(2PI)', 'a(4SIGMA+)'}, the string 'X(2PI)'
        needs to be fed into Isotopologue.set_ground_el_state_str, to identify, which
        of the resolved electronic states are the ground one.
        If the ground state is not set in the Isotopologue instance, feeding non-empty
        el_state_str will raise a StateError.

        If the vib_state_str is passed to the first State instance belonging to a
        certain Isotopologue, the Isotopologue.vib_state_dim gets populated with the
        dimension of the vibrational state vector.
        All other states created on the same Isotopologue instance need to match the
        same vibrational dimension, otherwise a StateError is raised.

        At least one of the two state strings need to be passed to any State instance
        and all the States belonging to one Isotopologue need to have consistent states
        (if all or none can have empty vib_state_str or all or none can have the empty
        el_state_str.)

        """
        if not el_state_str and not vib_state_str:
            raise StateError(
                "At least one of electronic or vibrational states needs to be "
                "specified!"
            )
        if vib_state_str and not vib_state_labels:
            raise StateError(
                "If vibrational states are resolved, both vib_state_str and "
                "vib_state_labels need to be passed!"
            )

        # ensure the passed el_state_str is valid and get canonicalised version and
        # html:
        el_state_str, _ = canonicalise_and_parse_el_state_str(el_state_str)
        # the following also ensures that the passed vib_state_str is valid
        vib_state_quanta, _ = validate_and_parse_vib_state_str(vib_state_str)
        vib_state_dim = len(vib_state_quanta)

        # state_str is only for error reporting:
        state_str = get_state_str(isotopologue, el_state_str, vib_state_str)

        # Only a single instance per isotopologue and both state_str should ever exist:
        try:
            cls.objects.get(
                isotopologue=isotopologue,
                el_state_str=el_state_str,
                vib_state_str=vib_state_str,
            )
            raise StateError(f'State "{state_str}" already exists!')
        except cls.DoesNotExist:
            pass

        # deal with the infinite lifetimes, swap for None
        if lifetime in {float("inf"), None}:
            lifetime = None
        elif lifetime < 0:
            raise StateError(
                f'Passed lifetime={lifetime} for State "{state_str}" is not positive!'
            )

        # check if the vibrational state dimension matches the other states of the
        # Isotopologue, the same with the vibrational quanta labels:
        if vib_state_dim:
            if not isotopologue.state_set.count():
                # first State being saved for the given isotopologue
                isotopologue.set_vib_quantum_labels(vib_state_labels)
                if isotopologue.vib_state_dim != vib_state_dim:
                    raise StateError(
                        f"vib_state_labels and vib_state_str do not agree in "
                        f"dimensions: {vib_state_labels}, {vib_state_str}, dimension "
                        f"detected was {vib_state_dim}!"
                    )
            elif isotopologue.vib_state_dim != vib_state_dim:
                raise StateError(
                    f"Vibrational dimension {vib_state_dim} of the state {state_str} "
                    f"does not match the vibrational dimension of the isotopologue "
                    f"{isotopologue}: {isotopologue.vib_state_dim}!"
                )
        elif isotopologue.vib_state_dim > 0:
            raise StateError(
                f"Isotopologue {isotopologue} expects vibrational dimension "
                f"{isotopologue.vib_state_dim}, but State {state_str} does not resolve "
                f"vibrational states!"
            )
        # the same check with the electronic state, if resolved, the Isotopologue needs
        # to know what a ground state is
        if el_state_str and not isotopologue.ground_el_state_str:
            raise StateError(
                f'Before saving State "{state_str}", ground_el_state_str needs to be '
                f"saved for Isotopologue {isotopologue}! Use "
                f"Isotopologue.set_ground_el_state_str() once before saving any states "
                f"resolving electronic excitation."
            )
        elif not el_state_str and isotopologue.ground_el_state_str:
            raise StateError(
                f"Isotopologue {isotopologue} has ground state defined and no "
                f"electronic state is passed to the State {state_str}! "
                f"This is not allowed for consistency, all the states belonging to one "
                f"Isotopologue must define either vib_state_str, or el_state_str, or "
                f"both. "
                f"This is reflected by Isotopologue instance by having "
                f"vib_state_dim > 0 or non-empty ground_el_state_str."
            )

        instance = cls(
            isotopologue=isotopologue,
            lifetime=lifetime,
            energy=energy,
            el_state_str=el_state_str,
            vib_state_str=vib_state_str,
        )
        instance.sync()
        return instance

    def get_html(self):
        molecule_html = self.isotopologue.molecule.html
        states_html = "; ".join(
            s for s in [self.el_state_html, self.vib_state_html] if s
        )
        return f"{molecule_html} {states_html}"

    @property
    def transition_set(self):
        from .transition import Transition

        return Transition.objects.filter(
            models.Q(initial_state=self) | models.Q(final_state=self)
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.isotopologue.sync(sync_only=["number_states"])
        for transition in self.transition_set.all():
            transition.sync(sync_only=["delta_energy"], save=False)
            # now I need to save the delta_energy without triggering Transition.save()
            # to avoid infinite recursion:
            transition.__class__.objects.filter(pk=transition.pk).update(
                delta_energy=transition.delta_energy
            )

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.isotopologue.sync(sync_only=["number_states"])
