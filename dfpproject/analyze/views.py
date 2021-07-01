from django.shortcuts import render
from . import models
from django.forms.models import model_to_dict
from database import models as db_model
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from database.filters import RecordFilter
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib import messages
import os
from utils import params, file_io
# Create your views here.
from django.views.generic import CreateView, ListView, TemplateView


class CreateTestset(SuccessMessageMixin, CreateView):
    template_name = 'analyze/create_testset.html'
    model = models.Testset
    fields = ('test_set_name', 'models_to_run', 'acts_to_run', 'testset_purporse')
    success_url = reverse_lazy('home')
    success_message = "Testset is created successfully!"

    def form_valid(self, form):

        # get selected data's primary keys
        pk_list = self.request.GET.getlist('checks')

        data_set_list = []

        for pk in pk_list:
            # get record
            record_obj = db_model.Records.objects.get(pk=pk)
            # append it as a dictionary
            data_set_list.append(record_obj.__dict__)

        # get test set object
        self.object = form.save(commit=False)
        # remove spaces in models_to_run string
        self.object.models_to_run = self.object.models_to_run.replace(' ', '')

        # set data set
        self.object.data_set = data_set_list

        # set result path

        """The program will save the results to the result directory """
        result_test_set_directory = os.path.join(params.ANALYZE_RESULTS_DIR, self.object.test_set_name)
        prob_result_directory = os.path.join(result_test_set_directory, "probs") # probs will saved under here
        self.object.results_path = result_test_set_directory  # store result directory.


        # Create folders that will be used to storing prob values.
        try:
            if not os.path.exists(result_test_set_directory):  # if file was not created.
                os.mkdir(result_test_set_directory)
                for model_id in self.object.models_to_run.split(','):
                    if model_id.isdigit():
                        file_io.create_folder(os.path.join(prob_result_directory, f"model_{model_id}"))

            else:
                messages.warning(self.request, message='This test data set has already been created.')
                return HttpResponseRedirect('/') # return back to home page with warning

        except Exception as err:
            messages.warning(self.request, message=err)
            return HttpResponseRedirect('/') # return back to home page with warning

        # save record
        self.object.save()

        return super().form_valid(form)




class RecordSelectSubset(ListView):
    model = db_model.Records
    template_name = "analyze/record_subset_list.html"
    context_object_name = "records"

    def get_queryset(self):
        qs = self.model.objects.all()
        filtered_list = RecordFilter(self.request.GET, queryset=qs)
        return filtered_list.qs


class AnalyzeTestSet(TemplateView):
    template_name = "analyze/analyze_options.html"

# return filter to the record_select_filter.html (filter result and filter form are shown in difference page.)
def select_subset_filter(request):
    f = RecordFilter(request.GET, queryset=models.Records.objects.all())
    return render(request, 'analyze/record_subset_filter.html', {'filter':f})
