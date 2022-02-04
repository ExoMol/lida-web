from django.db import models

from .exceptions import TransitionError
from .utils import BaseModel
from .state import State


class Transition(BaseModel):
    """A data model representing a transition between two states as a structure for
    partial lifetimes. Only a single Transition instance of any
    two initial and final states should exist at any given time in the database.
    To ensure this, it is recommended to use available class methods for creating
    new instances. The .get_from_* methods are also implemented to explicitly show what
    data uniquely identify each Transition instance.
    """

    initial_state = models.ForeignKey(
        State, on_delete=models.CASCADE, related_name="transition_from_set"
    )
    final_state = models.ForeignKey(
        State, on_delete=models.CASCADE, related_name="transition_to_set"
    )
    partial_lifetime = models.FloatField()

    sync_functions = {
        "delta_energy": lambda trans: trans.final_state.energy
        - trans.initial_state.energy,
    }

    delta_energy = models.FloatField()

    def __str__(self):
        return f"{self.initial_state} → {self.final_state}"

    @classmethod
    def get_from_states(cls, initial_state, final_state):
        """Example:
        initial_state = State.get_from_data(Isotopologue.get_from_data('CO'),
            vib_state_str='2'),
        final_state = State.get_from_data(Isotopologue.get_from_data('CO'),
            vib_state_str='1')
        """
        return cls.objects.get(initial_state=initial_state, final_state=final_state)

    @classmethod
    def create_from_data(cls, initial_state, final_state, partial_lifetime):
        """Example:
        initial_state = State.get_from_data(Isotopologue.get_from_data('CO'),
            vib_state_str='2'),
        final_state = State.get_from_data(Isotopologue.get_from_data('CO'),
            vib_state_str='1'),
        """
        if initial_state == final_state:
            raise TransitionError(f"Initial and final states must differ!")
        if initial_state.isotopologue is not final_state.isotopologue:
            raise TransitionError(
                f"Transition creation failed! States {initial_state} and {final_state} "
                f"do not share the same isotopologue!"
            )
        # Only a single instance per the states pair should ever exist:
        try:
            cls.get_from_states(initial_state, final_state)
            raise TransitionError(
                f"Transition({initial_state}, {final_state}) already exists!"
            )
        except cls.DoesNotExist:
            pass

        # values validation:
        if partial_lifetime < 0:
            raise TransitionError(
                f"Partial lifetime needs to be positive! Passed "
                f"partial_lifetime={partial_lifetime}!"
            )

        instance = cls(
            initial_state=initial_state,
            final_state=final_state,
            partial_lifetime=partial_lifetime
        )
        instance.sync()
        return instance

    def after_save_and_delete(self):
        self.initial_state.sync(sync_only=["number_transitions_from"])
        self.final_state.sync(sync_only=["number_transitions_to"])
        self.initial_state.isotopologue.sync(sync_only=["number_transitions"])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.after_save_and_delete()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.after_save_and_delete()
