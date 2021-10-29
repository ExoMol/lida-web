from django.db import models

from elida.apps.mixins import ModelMixin
from elida.apps.molecule.models import Isotopologue
from elida.apps.state.models import State
from .exceptions import TransitionError


class Transition(ModelMixin, models.Model):
    """A data model representing a transition between two states as a structure for partial lifetimes and branching
    ratios. Only a single Transition instance of any two initial and final states should exist
    at any given time in the database. To ensure this, it is recommended to use available class methods for creating
    new instances. The .get_from_* methods are also implemented to explicitly show what data uniquely identify each
    Transition instance.
    """
    initial_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='transition_from_set')
    final_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='transition_to_set')
    partial_lifetime = models.FloatField()
    branching_ratio = models.FloatField()

    sync_functions = {
        'delta_energy': lambda trans: trans.final_state.energy - trans.initial_state.energy,
        'initial_state_state_html': lambda trans: trans.initial_state.state_html,
        'final_state_state_html': lambda trans: trans.final_state.state_html,
        'html': lambda trans: f'{trans.initial_state.html} → {trans.final_state.html}'
    }

    delta_energy = models.FloatField()
    initial_state_state_html = models.CharField(max_length=128)  # simply copies initial_state.state_html
    final_state_state_html = models.CharField(max_length=128)  # simply copies final_state.state_html
    html = models.CharField(max_length=256)

    def __str__(self):
        return f'{self.initial_state} → {self.final_state}'

    @classmethod
    def get_from_states(cls, initial_state, final_state):
        """Example:
            initial_state = State.get_from_data(Isotopologue.get_from_data('CO'), vib_state_str='2'),
            final_state = State.get_from_data(Isotopologue.get_from_data('CO'), vib_state_str='1')
        """
        return cls.objects.get(initial_state=initial_state, final_state=final_state)

    @classmethod
    def create_from_data(cls, initial_state, final_state, partial_lifetime, branching_ratio):
        """Example:
            initial_state = State.get_from_data(Isotopologue.get_from_data('CO'), vib_state_str='2'),
            final_state = State.get_from_data(Isotopologue.get_from_data('CO'), vib_state_str='1'),
            partial_lifetime = 0.42e-42,
            branching_ratio = 0.42
        """
        if initial_state == final_state:
            raise TransitionError(f'Initial and final states must differ!')
        if initial_state.isotopologue is not final_state.isotopologue:
            raise TransitionError(f'Transition creation failed! States {initial_state} and {final_state} '
                                  f'do not share the same isotopologue!')
        # Only a single instance per the states pair should ever exist:
        try:
            cls.get_from_states(initial_state, final_state)
            raise TransitionError(f'Transition({initial_state}, {final_state}) already exists!')
        except cls.DoesNotExist:
            pass

        # values validation:
        if partial_lifetime < 0:
            raise TransitionError(f'Partial lifetime needs to be positive! Passed partial_lifetime={partial_lifetime}!')
        if branching_ratio < 0 or branching_ratio > 1:
            raise TransitionError(f'Branching ratio needs to be in [0, 1]! Passed branching_ratio={branching_ratio}!')

        instance = cls(initial_state=initial_state, final_state=final_state, partial_lifetime=partial_lifetime,
                       branching_ratio=branching_ratio)
        instance.sync(verbose=False)
        instance.save()
        return instance

    def after_save_and_delete(self):
        self.initial_state.sync(verbose=False, sync_only=['number_transitions_from'], propagate=False)
        self.initial_state.save()
        self.final_state.sync(verbose=False, sync_only=['number_transitions_to'], propagate=False)
        self.final_state.save()
        self.initial_state.isotopologue.sync(verbose=False, sync_only=['number_transitions'])
        self.initial_state.isotopologue.save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.after_save_and_delete()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.after_save_and_delete()

    def sync(self, verbose=False, sync_only=None, skip=None):
        """Runs all the sync_functions on the relevant fields. See the the method in the ModelMixin for documentation.
        Warning: Does not call save, must be saved after sync is called!"""
        super().sync(verbose=verbose, sync_only=sync_only, skip=skip)
