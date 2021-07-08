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
from decorators.decorators import timer
import os
import shutil
from analyze.dpu import Dpu
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
        power_result_directory = os.path.join(result_test_set_directory, "powers")
        self.object.results_path = result_test_set_directory  # store result directory.


        # Create folders that will be used to storing prob values.
        try:
            if not os.path.exists(result_test_set_directory):  # if file was not created.
                os.mkdir(result_test_set_directory)
                for model_id in self.object.models_to_run.split(','):
                    if model_id.isdigit():
                        file_io.create_folder(os.path.join(prob_result_directory, f"model_{model_id}"))
                file_io.create_folder(power_result_directory)

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


class SelectTestSet(ListView):
    template_name = "analyze/select_testset.html"
    context_object_name = "testsets"
    model = models.Testset



class AnalyzeTestSet(TemplateView):
    template_name = "analyze/analyze_options.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_pk'] = self.request.GET.getlist('radio_check')[0]
        return context


# return filter to the record_select_filter.html (filter result and filter form are shown in difference page.)
def select_subset_filter(request):
    f = RecordFilter(request.GET, queryset=models.Records.objects.all())
    return render(request, 'analyze/record_subset_filter.html', {'filter':f})




def is_power_prob_extracted(results_path, model_result_path, raw_data_file_name) -> bool:
    prob_files = os.listdir(model_result_path)
    pow_files = os.listdir(os.path.join(results_path, "powers"))
    if any([raw_data_file_name + "_power.pow" in f for f in pow_files]) and any([raw_data_file_name +
                                                                                 "_prob.prob" in f for f in prob_files]):
        return True
    return False


# calculate power prob for selected test set
@timer
def calculate_power_prob(request, pk):
    # get test set object
    test_set = models.Testset.objects.get(pk=pk)
    data_set = test_set.data_set

    # init some values
    extension_list = ['_power.pow', '_prob.prob', '.detections', '.result', '_alarms.txt', '_dpu_time_log.txt']
    # init Dpu class
    dpu = Dpu()
    print(dpu)
    models_to_run = test_set.models_to_run.split(',')
    results_path = test_set.results_path
    powers_folder_path = os.path.join(results_path, "powers")
    probs_folder_path = os.path.join(results_path, "probs")

    for model_id in models_to_run:
        is_any_data_processed = False  # this variable is used to understand if any data was processed for given model.
        model_results_folder_path = os.path.join(probs_folder_path, "model_" + str(model_id))
        prob_results_folder_path = os.path.join(model_results_folder_path, "prob_results")
        if not os.path.exists(prob_results_folder_path):
            file_io.create_folder(prob_results_folder_path)
        if not os.path.exists(powers_folder_path):
            file_io.create_folder(powers_folder_path)
        # set category number.
        category_num = -1
        # convert model_id to int
        model_id = int(model_id)
        if model_id == 0:
            category_num = 14  # indicates the number of activities (digging, walking ext.)
        elif model_id in [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 19]:
            category_num = 5
        assert (category_num == 5 or category_num == 14)

        for data_idx, data_doc in enumerate(data_set):

            # get some features about raw data.
            raw_data_path = data_doc["data_full_path"]
            # extract the file name. [1] used to take the tail part
            raw_data_file_name = os.path.split(raw_data_path)[1]
            # check if the power and the prob results have already been extracted by the specified data.
            if is_power_prob_extracted(results_path, prob_results_folder_path, raw_data_file_name):
                continue
            is_any_data_processed = True
            start_channel = data_doc['start_channel']
            channel_num = data_doc["channel_num"]
            record_size = data_doc["record_size"]
            iter_num = record_size / (2*channel_num*400)
            assert (round(iter_num) == iter_num)  # iter num supposed to be an integer
            print('iteration number in the record is ' + str(iter_num))
            # set dpu config parameters
            dpu.set_config_params(raw_data_file_path=raw_data_path, model_id=model_id, category_num=category_num,
                                  channel_num=channel_num, start_channel=start_channel,
                                  filter_id=1, tracker_mode_on=False)
            # run dpu

            err = dpu.run()
            if err:
                messages.error(request, message="Error in dpu run")
                return HttpResponseRedirect('/') # return back to home page with warning

            """
            dpu automatically saves the power and the prob results under the raw data file path.
            Move these results under the model_results_folder_path
            """
            for ext in extension_list:
                try:
                    # move
                    if ext == '_power.pow':
                        destination = os.path.join(powers_folder_path, raw_data_file_name + ext)
                        if not os.path.exists(destination):
                            shutil.move(raw_data_path + ext, destination)
                    else:
                        shutil.move(raw_data_path+ext, os.path.join(prob_results_folder_path, raw_data_file_name+ext))

                except FileNotFoundError:
                    pass
            print('end of processing ' + str(data_idx) + 'th data, e.g. ' + raw_data_path)

        if is_any_data_processed:  # if any data is processed for current model.
            # save config parameters, which are used to execute dpu, into the model results file.
            # create config folder
            save_config_path = os.path.join(prob_results_folder_path, "config\\default")
            file_io.create_folder(save_config_path)
            # copy config values
            for file_name in os.listdir(dpu.config_params_default_path):
                try:
                    shutil.copy(os.path.join(dpu.config_params_default_path, file_name), save_config_path)
                except FileNotFoundError:
                    pass
                    # print(e)
            print('config settings during dpu run saved under ' + save_config_path)


    if dpu.n_of_run == 0:
        messages.warning(request, message="This test set data power and prob values have already been extracted.")
        return HttpResponseRedirect('/') # return back to home page with warning

    messages.success(request, message=f"Power and prob data are calculated for given test set. Number of DPU Run:{dpu.n_of_run}")
    return HttpResponseRedirect('/') # return back to home page with warning


def calculate_roc_curves(request, pk):
        # get test set object
        test_set = models.Testset.objects.get(pk=pk)
        data_set = test_set.data_set
