from django.shortcuts import render
from django.views.generic import CreateView
from django.urls import reverse_lazy
from . import forms
from utils.file_io import read_json
from pathlib import Path

# Create your views here.

dynamic_doc_path =   Path(__file__).resolve().parent.parent / 'json_files' / 'dynamic_document_values.json'

class InsertRecord(CreateView):
    form_class = forms.RecordCreateForm
    success_url = reverse_lazy('home')
    template_name = 'dfpapp/record_form.html'


def load_regions(request): # load list of regions for given project
    dynamic_doc = read_json(dynamic_doc_path) # read dynamic doc
    project = request.GET.get('project') # fetch selected project
    regions = dynamic_doc[f"region_{project}"] # find project specific regions
    return render(request, 'dfpapp/region_dropdown_list_options.html', {'regions': regions}) # render back
