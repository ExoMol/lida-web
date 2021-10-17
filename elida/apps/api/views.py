from django.shortcuts import render
from django.http import HttpResponse


# Create your views here.

def about(request):
    return render(request, 'api_about.html', context={'title': 'API'})
