from django.db import models
from pyvalem.formula import Formula as PVFormula

from .exceptions import MoleculeError
from .utils import BaseModel


class Molecule(BaseModel):
    """A data model representing a molecule of a stateless species, without regards to
    different isotopologues.
    It is highly recommended to only use the available class methods to interact with
    the database (get_from_* and create_from_*), as these are coded to handle the name
    canonicalization etc.
    """

    # The following fields should be compatible with ExoMol database itself (and the
    # formula_str needs to be compatible with pyvalem.formula.Formula)
    formula_str = models.CharField(max_length=16)
    name = models.CharField(max_length=64, default="")

    sync_functions = {
        "slug": lambda molecule: PVFormula(molecule.formula_str).slug,
        "html": lambda molecule: PVFormula(molecule.formula_str).html,
        "charge": lambda molecule: PVFormula(molecule.formula_str).charge,
        "number_atoms": lambda molecule: PVFormula(molecule.formula_str).natoms,
    }

    slug = models.CharField(max_length=16)
    html = models.CharField(max_length=64)
    charge = models.SmallIntegerField()
    number_atoms = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.formula_str

    @classmethod
    def get_from_formula_str(cls, formula_str):
        """The formula_str needs to be canonicalised formula compatible with
        pyvalem.formula.Formula argument.
        It is expected that only a single Molecule instance with a given formula_str
        exists, otherwise this might lead to inconsistent behaviour.
        """
        return cls.objects.get(formula_str=formula_str)

    @classmethod
    def create_from_data(cls, formula_str, name=""):
        """A method for creation of new Molecule instances. It is highly recommended to
        use this method to prevent multiple Molecule duplicates, inconsistent fields,
        etc.
        Example:
            formula_str = 'H2O',
            name = 'Water'
        The arguments should be compatible with ExoMol database itself.
        """
        pyvalem_formula = PVFormula(formula_str)

        # ensure the passed formula_str is canonicalised (canonicalisation offloaded to
        # pyvalem)
        if repr(pyvalem_formula) != formula_str:
            raise MoleculeError(
                f"Non-canonicalised formula {formula_str} passed, "
                f"instead of {repr(pyvalem_formula)}"
            )

        try:
            cls.get_from_formula_str(formula_str)
            # Only a single instance with the given formula_str should exist!
            raise MoleculeError(f"Molecule({formula_str}) already exists!")
        except cls.DoesNotExist:
            pass

        instance = cls(formula_str=formula_str, name=name)
        instance.sync()
        return instance
