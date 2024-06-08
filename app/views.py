"""
Definition of views.
"""

from datetime import datetime
from django.shortcuts import render
from django.http import HttpRequest
from .device import DeviceHandler

def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/index.html',
        {
            'title':'Home Page',
            'year':datetime.now().year,
        }
    )

def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/contact.html',
        {
            'title':'Contact',
            'year':datetime.now().year,
        }
    )

def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/about.html',
        {
            'title':'About',
            'year':datetime.now().year,
        }
    )

def devices(request):
    """Renders the devices list page."""
    assert isinstance(request, HttpRequest)
    handler = DeviceHandler()
    devices = handler.get_devices()
    date = datetime.now()
    return render(
        request,
        'app/devices.html',
        {
            'title':'Device Status',
            'year':date.year,
            'devices':devices,
            'date':date
        }
    )