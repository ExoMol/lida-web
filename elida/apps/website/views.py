from django.shortcuts import render


def home(request):
    return render(request, 'about.html')


def data(request):
    return render(request, 'data.html', context={'title': 'Data'})


def about(request):
    return render(request, 'about.html', context={'title': 'About'})


def contact(request):
    return render(request, 'contact.html', context={'title': 'Contact'})
