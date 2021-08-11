from django.shortcuts import render
from django.views.generic import TemplateView
# Create your views here.


class AddUseCase(TemplateView):
    template_name = "filesystem/add_use_case.html"
