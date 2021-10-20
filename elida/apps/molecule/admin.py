from django.contrib import admin
from .models import Molecule, Isotopologue

# Register your models here.
admin.site.register(Molecule)
admin.site.register(Isotopologue)
