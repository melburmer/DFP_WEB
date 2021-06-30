from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView

class AnalyzePage(TemplateView):
    template_name = 'analyze/deneme.html'
