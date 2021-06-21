from django.shortcuts import render
from django.views.generic import CreateView
from django.urls import reverse_lazy
from . import forms

# Create your views here.

class InsertRecord(CreateView):
    form_class = forms.RecordCreateForm
    success_url = reverse_lazy('home')
    template_name = 'dfpapp/record_form.html'
