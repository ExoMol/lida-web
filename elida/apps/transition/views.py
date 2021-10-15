from django.shortcuts import render


# Create your views here.
def details(request):
    return render(request, 'transition_details.html')
