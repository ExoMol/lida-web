from django.shortcuts import render
from django.http import HttpResponse


# Create your views here.
def details(request):
    return render(request, 'molecule_details.html')
