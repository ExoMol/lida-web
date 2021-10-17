from django.shortcuts import render


def home(request):
    return render(request, 'website_about.html')


def data(request):
    return render(request, 'wibsite_data.html', context={'title': 'Data'})


def about(request):
    return render(request, 'website_about.html', context={'title': 'About'})


def contact(request):
    return render(request, 'website_contact.html', context={'title': 'Contact'})
