from django.contrib import admin

from .models import Molecule, Isotopologue, State, Transition

# Register your models here.
admin.site.register(Molecule)
admin.site.register(Isotopologue)
admin.site.register(State)
admin.site.register(Transition)
