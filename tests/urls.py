"""Trivial URLconf for the wagtail-starling test suite."""

from django.http import HttpResponse
from django.urls import path


def _home(request):
    return HttpResponse("ok")


urlpatterns = [path("", _home)]
