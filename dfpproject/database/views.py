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
    template_name = 'database/record_form.html'


def load_regions(request): # load list of regions for given project
    dynamic_doc = read_json(dynamic_doc_path) # read dynamic doc
    project = request.GET.get('project') # fetch selected project
    if project: # if project field is selected
        regions = dynamic_doc[f"region_{project}"] # find project specific regions
    else:
        regions = ""

    return render(request, 'database/region_dropdown_list_options.html', {'regions': regions}) # render back

# load list of activity type for given fo_use_case
def load_act_types(request):
    dynamic_doc = read_json(dynamic_doc_path) # read dynamic doc
    fo_use_case = request.GET.get('fo_use_case') # fetch selected fo use case
    if fo_use_case:
        acts = dynamic_doc[f"activity_type_{fo_use_case}"]
    else:
        acts = ""
    return render(request, 'database/act_dropdown_list_options.html', {'acts':acts})


# view to load activity specifications
def load_actspecs(request):
    dynamic_doc = read_json(dynamic_doc_path) # read dynamic doc
    activity = request.GET.get('activity') # fetch selected act
    if activity:
        try:
            actspecs = dynamic_doc[f'activity_specification_{activity}']

        except KeyError: # if act-specfication is not defined for selected act
            actspecs = ""
    else:
        actspecs = ""
    return render(request, 'database/actspecs_dropdown_list_options.html', {'actspecs':actspecs})
