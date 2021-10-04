from django.db import models
from pyvalem.formula import Formula as PVFormula
from pyvalem.stateful_species import StatefulSpecies as PVStatefulSpecies

from utils.models import ProvenanceMixin


class Formula(ProvenanceMixin, models.Model):
    id = models.AutoField(primary_key=True)

    formula_str = models.CharField(max_length=16)
    name = models.CharField(max_length=64)

    html = models.CharField(max_length=64)
    charge = models.SmallIntegerField()
    natoms = models.SmallIntegerField()

    @classmethod
    def get_from_formula_str(cls, formula_str):
        return cls.objects.get(formula_str=formula_str)

    @classmethod
    def create_from_data(cls, formula_str, name):
        pyvalem_formula = PVFormula(formula_str)

        # ensure the passed formula_str is canonicalised (canonicalisation offloaded to pyvalem)
        if repr(pyvalem_formula) != formula_str:
            raise ValueError(f'Non-canonicalised formula {formula_str} passed, instead of {repr(pyvalem_formula)}')

        try:
            cls.get_from_formula_str(formula_str)
            raise ValueError(f'{cls.__name__}({formula_str}) already exists!')
        except cls.DoesNotExist:
            pass

        cls.objects.create(formula_str=formula_str, name=name, html=pyvalem_formula.html,
                           charge=pyvalem_formula.charge, natoms=pyvalem_formula.natoms)


class Isotopologue(ProvenanceMixin, models.Model):
    id = models.AutoField(primary_key=True)
    formula = models.ForeignKey(Formula, on_delete=models.CASCADE)

    iso_formula_str = models.CharField(max_length=32)
    iso_slug = models.CharField(max_length=32)
    inchi_key = models.CharField(max_length=32)
    dataset_name = models.CharField(max_length=16)
    version = models.PositiveIntegerField()

    html = models.CharField(max_length=64)
    mass = models.FloatField()

    @classmethod
    def get_from_iso_formula_str(cls, iso_formula_str):
        return cls.objects.get(iso_formula_str=iso_formula_str)

    @classmethod
    def create_from_data(cls, formula_instance, iso_formula_str, inchi_key, dataset_name, version):
        pyvalem_formula = PVFormula(iso_formula_str)

        # ensure the passed formula_str is canonicalised (canonicalisation offloaded to pyvalem)
        if repr(pyvalem_formula) != iso_formula_str:
            raise ValueError(f'Non-canonicalised formula {iso_formula_str} passed, instead of {repr(pyvalem_formula)}')

        try:
            cls.get_from_iso_formula_str(iso_formula_str)
            raise ValueError(f'{cls.__name__}({iso_formula_str}) already exists!')
        except cls.DoesNotExist:
            pass

        cls.objects.create(formula=formula_instance, iso_formula_str=iso_formula_str, iso_slug=pyvalem_formula.slug,
                           inchi_key=inchi_key, dataset_name=dataset_name, version=version, html=pyvalem_formula.html,
                           mass=pyvalem_formula.mass)


class State(ProvenanceMixin, models.Model):
    id = models.AutoField(primary_key=True)
    isotopologue = models.ForeignKey(Isotopologue, on_delete=models.CASCADE)

    state_str = models.CharField(max_length=64)
    energy = models.FloatField()

    html = models.CharField(max_length=128)

    @classmethod
    def get_from_data(cls, isotopologue_instance, state_str):
        return cls.objects.get(isotopologue=isotopologue_instance, state_str=cls.canonicalise_state_str(state_str))

    @classmethod
    def create_from_data(cls, isotopologue_instance, state_str, energy):
        pyvalem_species = PVStatefulSpecies(f'{isotopologue_instance.iso_formula_str} {state_str}')
        sp_str, canonicalised_state_str = repr(pyvalem_species).split(' ')
        assert sp_str == isotopologue_instance.iso_formula_str, 'This should never be raised, only a defense!'
        try:
            cls.objects.get(isotopologue=isotopologue_instance, state_str=canonicalised_state_str)
            raise ValueError(f'{cls.__name__}({isotopologue_instance}, {canonicalised_state_str}) already exists!')
        except cls.DoesNotExist:
            pass

        cls.objects.create(isotopologue=isotopologue_instance, state_str=canonicalised_state_str, energy=energy,
                           html=pyvalem_species.html)

    @staticmethod
    def canonicalise_state_str(state_str):
        test_species = 'M'
        canonicalised_state_str = repr(PVStatefulSpecies(f'{test_species} {state_str}')).lstrip('M').strip()
        return canonicalised_state_str

# TODO: write docstrings!
# TODO: write some unittests!
