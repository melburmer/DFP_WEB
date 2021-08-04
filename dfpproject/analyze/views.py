from django.shortcuts import render, redirect
from . import models, visualize
from django.forms.models import model_to_dict
from database import models as db_model
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from database.filters import RecordFilter
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib import messages
from decorators.decorators import timer
from scipy import ndimage
import os
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np
import shutil
from analyze.dpu import Dpu
from utils import params, file_io, das_util
# Create your views here.
from django.views.generic import CreateView, ListView, TemplateView
from scipy import signal
from plotly.subplots import make_subplots


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
        test_set_name = test_set.test_set_name
        models_to_run = test_set.models_to_run
        acts_to_run = test_set.acts_to_run
        data_set = test_set.data_set
        result_folder_path = test_set.results_path

        # read params for analysis
        ANALYZE_PARAMS = file_io.read_json("json_files/analyze/analyze_params.json")
        reset_on = ANALYZE_PARAMS["reset_on"]
        probs_folder_path = os.path.join(result_folder_path, "probs")  # probs results path
        extracted_powers_folder_path = os.path.join(result_folder_path, "powers")

        dict_models = {}  # it will be used to store models' results.
        is_any_data_analyzed = False

        models_to_run = models_to_run.split(',') # models to run stored as "1,2,3", so split it and create list
        for model_idx, model_id in enumerate(models_to_run):
            model_id = int(model_id)
            dict_models['model_' + str(model_id)] = {}
            model_results_folder_path = os.path.join(probs_folder_path, "model_" + str(model_id))
            extracted_probs_folder_path = os.path.join(model_results_folder_path, "prob_results") # prob files saved under here.
            if not os.path.exists(extracted_probs_folder_path):
                # if there isn't any power and prob data for the specified model
                print(f"Cannot find prob data for the model_{model_id}")
                # continue to the next model
                continue
            if not os.path.exists(extracted_powers_folder_path):
                # if there isn't any power and prob data for the specified model
                messages.warning(request, message=f"Cannot find power data for the test set: {test_set_name}")
                return HttpResponseRedirect('/') # return back to home page with warning

            analysis_result_folder_path = os.path.join(model_results_folder_path, "act_count_analysis")  # analysis results will be saved here.


            if not os.path.exists(analysis_result_folder_path):
                file_io.create_folder(analysis_result_folder_path)  # create if it isn't exist
                    # set category number.
            category_num = -1
            if model_id == 0:
                category_num = 14
            elif model_id in [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 19, 20]:
                category_num = 5
            else:
                messages.error(request, message=f"Model : is not a valid model. Please check available models.")
                return HttpResponseRedirect('/') # return back to home page with error

            dict_all_data = {}  # this dictionary will used to store results of all data.

            for data_idx, data_doc in enumerate(data_set):
                raw_data_file_name = data_doc["file_name"]
                # _, raw_data_file_name = os.path.split(data_doc["data_full_path"])
                # Skip for loop if the power and the prob values weren't extracted for the given raw data.
                if not is_power_prob_extracted(result_folder_path, extracted_probs_folder_path, raw_data_file_name):
                    continue

                is_any_data_analyzed = True
                dict_all_data['idx_'+str(data_idx)] = {}

                # get some features about raw data.
                raw_data_path = data_doc["data_full_path"]
                record_type = data_doc["record_type"]
                activity_type = data_doc["activity"]
                start_channel = data_doc['start_channel']
                channel_num = data_doc["channel_num"]
                activity_channel = int(data_doc['activity_channel'])
                activity_channel_from_start = activity_channel - start_channel
                if activity_channel_from_start < 0:
                    messages.error(request, message=f" Activity channel cannot be greater than start channel, data_path:{raw_data_path}")
                    return HttpResponseRedirect('/')

                # set ground truth
                ground_truth = activity_type
                if record_type == "alarm_triggered":
                    ground_truth = "at"  # set ground truth as alarm triggered.
                elif activity_type == "human":
                    try:
                        if data_doc["activity_specification"] == "tum_saha_yurume":
                            ground_truth = "tum_saha_yurume"
                    except KeyError:
                        ground_truth = activity_type

                # analysis results of given data will be saved under the analysis result path with the .analysis extension.
                data_analysis_result_path = os.path.join(analysis_result_folder_path, raw_data_file_name + ".analysis")

                try:
                    data_analysis_results_dict = file_io.read_json(data_analysis_result_path)
                except FileNotFoundError:
                    data_analysis_results_dict = {f"model_{model_id}": {}}

                if 'model_' + str(model_id) not in data_analysis_results_dict:
                    data_analysis_results_dict['model_' + str(model_id)] = {}


                dict_all_acts_rec = data_analysis_results_dict['model_' + str(model_id)]

                dict_all_acts = {"raw_data_path": raw_data_path, "ground_truth": ground_truth}

                """ read norm power for given data"""
                power_data_path = os.path.join(extracted_powers_folder_path, raw_data_file_name+'_power.pow')
                power_time_start_idx = ANALYZE_PARAMS["power_time_start_idx"]
                power_time_end_idx = ANALYZE_PARAMS["end_time_in_secs"]*2*ANALYZE_PARAMS["fs_power_data"]
                all_power_data = das_util.read_norm_power(power_data_path, channel_start=0, channel_end=channel_num,
                                                          time_start_idx=power_time_start_idx,
                                                          time_end_idx=power_time_end_idx, channel_num=channel_num)
                norm_power_data = all_power_data[1::2, ::]


                """read prob for given data"""
                prob_data_path = os.path.join(extracted_probs_folder_path, raw_data_file_name + '_prob.prob')
                prob_time_start_idx = ANALYZE_PARAMS["prob_time_start_idx"]
                prob_time_end_idx = ANALYZE_PARAMS["end_time_in_secs"] * ANALYZE_PARAMS["fs_prob_data"]


                all_prob_data = das_util.read_all_prob_data(prob_data_path, channel_start=0, channel_end=channel_num,
                                                            time_start_idx=prob_time_start_idx,
                                                            time_end_idx=prob_time_end_idx, channel_num=channel_num,
                                                            category_num=category_num)

                power_data_offset = ANALYZE_PARAMS["power_data_offset"]

                # map prob data. read prob data with proper format.
                prob_data_mapped = das_util.map_prob_data(prob_data=all_prob_data, power_data=norm_power_data,
                                                          category_num=category_num,
                                                          enable_cutter_for_exc=ANALYZE_PARAMS["enable_cutter_for_exc"],
                                                          power_data_offset=power_data_offset)

                for cur_act in acts_to_run:
                    # find appropriate index to use fetch analyze params for current act.
                    act_type_index = ANALYZE_PARAMS["activity_names"].index(cur_act)
                    act_range = ANALYZE_PARAMS["activity_range_vals"][act_type_index]
                    act_prob_threshes = ANALYZE_PARAMS["activity_prob_threshes"][act_type_index]

                    dict_all_acts[cur_act] = {}

                    if ground_truth == "long" or ground_truth == "at" or ground_truth == "tum_saha_yurume":
                        # process all data
                        act_start = 0
                        act_end = channel_num
                    else:
                        act_start = max(0, activity_channel_from_start-act_range)
                        act_end = min(activity_channel_from_start+act_range+1, channel_num)

                    # check if the current act has already been processed.
                    if cur_act in dict_all_acts_rec and 'channel_indices' in dict_all_acts_rec[cur_act]:
                        channel_indices_rec = dict_all_acts_rec[cur_act]['channel_indices']
                        cur_prob_threshes_rec = dict_all_acts_rec[cur_act]['prob_threshes']
                        cur_channel_indices = list(np.arange(act_start, act_end))
                        if (len(cur_prob_threshes_rec) == len(act_prob_threshes) and
                           sum(np.array(sorted(cur_prob_threshes_rec))-np.array(sorted(act_prob_threshes))) == 0 and
                           len(channel_indices_rec) == len(cur_channel_indices) and
                           sum(np.array(sorted(channel_indices_rec))-np.array(sorted(cur_channel_indices))) == 0 and
                           not reset_on):
                            dict_all_acts[cur_act] = dict_all_acts_rec[cur_act]
                            continue

                    max_act_count_nums, thresh_pass_nums = das_util.find_counts(prob_data_mapped=prob_data_mapped,
                                                                                norm_power_data=norm_power_data, act=cur_act,
                                                                                act_start=act_start, act_end=act_end,)

                    dict_all_acts[cur_act]['channel_indices'] = np.arange(act_start, act_end).tolist()
                    dict_all_acts[cur_act]['prob_threshes'] = act_prob_threshes
                    different_prob_num = len(act_prob_threshes)
                    for act_prob_idx in range(different_prob_num):
                        s_data = {'all_vals_passing_thresh': thresh_pass_nums[:, act_prob_idx].tolist(),
                                  'max_act_count_numbers': max_act_count_nums[:, act_prob_idx].tolist()}
                        # note:
                        # 'all_vals_passing_thresh': total number of passing trehsh values for specified channel
                        # 'max_act_count_numbers' max count for specified channel
                        act_prob = act_prob_threshes[act_prob_idx]
                        dict_all_acts[cur_act]['prob_' + str(round(act_prob * 100))] = s_data

                    print(cur_act + ' completed')
                data_analysis_results_dict['model_' + str(model_id)] = dict_all_acts
                file_io.save_to_json(data_analysis_results_dict, data_analysis_result_path)
                dict_all_data["idx_"+str(data_idx)] = dict_all_acts
                print('data id: {}, data progress: {}/{}; {}/{}'.format(data_idx, data_idx+1,
                                                                        len(data_set),
                                                                        model_idx+1, len(models_to_run)))
            dict_models['model_'+str(model_id)] = dict_all_data

            print('model id: {}, model progress: {}/{}'.format(model_id, model_idx + 1, len(models_to_run)))

        if is_any_data_analyzed:
            date = file_io.get_datetime()
            test_set_models_result_path = os.path.join(result_folder_path, "roc_curves_results--"+date)
            file_io.create_folder(test_set_models_result_path)
            analysis_json_to_save_path = os.path.join(test_set_models_result_path, "analyses_res.info")
            file_io.save_to_json(dict_models, analysis_json_to_save_path)
            visualize.visualize_roc_curves(analysis_json_to_save_path, models_to_run, acts_to_run, test_set_models_result_path)
        else:
            messages.warning(request, message="The power and the prob values have not been extracted for any data in this test set.")
            return HttpResponseRedirect('/')

        return HttpResponseRedirect('/')


def select_test_data_subset(request, caller_id, pk):
    # get test set object
    test_set = models.Testset.objects.get(pk=pk)
    data_set = test_set.data_set

    return render(request, "analyze/select_test_data_subset.html",
                {'data_set':data_set, 'pk':pk, 'caller_id':caller_id})


def route_selected_testset_subset(request, caller_id, test_set_pk):
    selected_data_hash_list = request.POST.getlist('checks')
    # store it into the session to use in another view
    request.session['selected_data_hash_list'] = selected_data_hash_list
    # get start and end channel inputs
    start_channels = {}
    end_channels = {}


    for hash_val in selected_data_hash_list:
        start_channels[hash_val] = request.POST.get('start_'+ str(hash_val))
        end_channels[hash_val] = request.POST.get('end_'+ str(hash_val))

    # add start and end channel inputs to the session.
    request.session['start_channels'] = start_channels
    request.session['end_channels'] = end_channels

    # route subset data to the functions based on caller id.
    if caller_id == 2:
        # redirect selected data to the visualize power prob
        return redirect("analyze:visualize_power_prob", test_set_pk=test_set_pk)

    if caller_id == 3:
        # redirect selected data to the visualize spectrogram
        return redirect("analyze:visualize_spectrogram", test_set_pk=test_set_pk)

def visualize_power_prob(request, test_set_pk):

    # get some params to visualization
    VIS_POWER_PROB_PARAMS = file_io.read_json("json_files/analyze/power_prob_visualize_params.json")
    activity_indices = VIS_POWER_PROB_PARAMS["activity_indices"]
    activity_names = VIS_POWER_PROB_PARAMS["activity_names"]
    activity_prob_threshes = VIS_POWER_PROB_PARAMS["activity_prob_threshes"]
    activity_norm_power_threshes = VIS_POWER_PROB_PARAMS["activity_norm_power_threshes"]
    activity_windows = VIS_POWER_PROB_PARAMS["activity_windows"]
    fs_norm_power = VIS_POWER_PROB_PARAMS["fs_norm_power"]
    time_end_idx = 5 * 60 * 60 * fs_norm_power  # 5 hours
    im_show_off = False
    colormap = plt.get_cmap('jet')

    # get data to visualize
    selected_data_hash_list = request.session['selected_data_hash_list']
    if not selected_data_hash_list: # if user do not select any data
        messages.warning(request, message="Please select data")
        return HttpResponseRedirect('/')

    # read vis start and vis and channels
    vis_start_channels = request.session['start_channels']
    vis_end_channels = request.session['end_channels']

    test_set = models.Testset.objects.get(pk=test_set_pk).__dict__
    models_to_run = test_set["models_to_run"]
    models_to_run = models_to_run.split(',') # models to run stored as "1,2,3", so split it and create list
    acts_to_run = test_set["acts_to_run"]
    data_set = test_set["data_set"]
    results_path = test_set["results_path"]
    probs_folder_path = os.path.join(results_path, "probs")  # probs are under here.
    power_results_folder_path = os.path.join(results_path, "powers")  # powers are under here.
    #colormap = plt.get_cmap('jet')


    is_any_data_analyzed = False
    # foreach model
    for model_idx, model_id in enumerate(models_to_run):
        model_id = int(model_id)
        # get model prob results folder path
        model_results_folder = os.path.join(probs_folder_path, "model_"+str(model_id))
        prob_results_folder_path = os.path.join(model_results_folder, "prob_results")
        if not os.path.exists(prob_results_folder_path):
            print(f"Prob results for model{model_id} are not exists")
            continue

        category_num = -1
        if model_id == 0:
            category_num = 14
        elif model_id in [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 19]:
            category_num = 5
        else:

            messages.warning(request, message=f"Model cannot be found, Model Id: {model_id}")
            return HttpResponseRedirect('/') # return back to home page with warning

        for data_idx, data_doc in enumerate(data_set):
            if data_doc["bin_file_hash"] in selected_data_hash_list:
                # read start and end channels of given data for visualisation.

                if vis_start_channels[data_doc["bin_file_hash"]] == "" or vis_start_channels[data_doc["bin_file_hash"]].isdigit() == False or int(vis_start_channels[data_doc["bin_file_hash"]])<0:
                    vis_start_ch = data_doc["start_channel"]
                else:
                    #  if start channel didnt given.
                    vis_start_ch = int(vis_start_channels[data_doc["bin_file_hash"]])

                if vis_end_channels[data_doc["bin_file_hash"]] == "" or vis_end_channels[data_doc["bin_file_hash"]].isdigit() == False or int(vis_end_channels[data_doc["bin_file_hash"]])>5150:
                    vis_end_ch = data_doc["end_channel"]
                else:
                    #  if end channel didnt given.
                    vis_end_ch = int(vis_end_channels[data_doc["bin_file_hash"]])

                if vis_end_ch < vis_start_ch:
                    # set default start and end channels
                    vis_start_ch = data_doc["start_channel"]
                    vis_end_ch = data_doc["end_channel"]
                start_channel = data_doc["start_channel"]
                end_channel = data_doc["end_channel"]
                channel_num = data_doc["channel_num"]
                activity_channel = data_doc["activity_channel"]
                raw_data_file_name = data_doc["file_name"]

                # Skip for loop if the power and the prob values were not extracted for the given raw data.
                if not is_power_prob_extracted(results_path, prob_results_folder_path, raw_data_file_name):
                    continue
                is_any_data_analyzed = True  # This variable will be False if all selected data are skipped.

                for cur_act in acts_to_run:
                    act_idx = activity_names.index(cur_act)
                    cur_prob_threshes = activity_prob_threshes[act_idx]
                    cur_category_idx = activity_indices[act_idx]
                    cur_window_size = activity_windows[act_idx]
                    cur_norm_power_thresh = activity_norm_power_threshes[act_idx]

                    # images will be saved under the img_results_folder_path
                    img_results_folder_path = os.path.join(results_path, "power_prob_visualisation")
                    if not os.path.exists(img_results_folder_path):  # crete image output folder if not exist.
                        file_io.create_folder(img_results_folder_path)

                    """ read norm power for given data"""
                    cur_power_data_path = os.path.join(power_results_folder_path, raw_data_file_name+'_power.pow')
                    cur_power_data = das_util.read_norm_power(cur_power_data_path, channel_start=vis_start_ch,
                                                              channel_end=vis_end_ch, time_start_idx=0,
                                                              time_end_idx=2*time_end_idx, channel_num=channel_num)
                    cur_norm_power = cur_power_data[1::2, :]
                    min_norm_power = -30
                    max_norm_power = 30
                    cur_norm_power = cur_norm_power.clip(min_norm_power, max_norm_power)

                    """read prob for given data"""
                    cur_prob_data_path = os.path.join(prob_results_folder_path, raw_data_file_name + '_prob.prob')
                    cur_prob_data = das_util.read_prob_data(cur_prob_data_path, channel_start=vis_start_ch,
                                                            channel_end=vis_end_ch, time_start_idx=0,
                                                            time_end_idx=time_end_idx, channel_num=channel_num,
                                                            category_num=category_num, category_idx=cur_category_idx)

                    prob_data_row_num = cur_prob_data.shape[0]
                    real_cur_window_size = min(prob_data_row_num, cur_window_size)
                    cur_kernel = np.ones((real_cur_window_size, 1))

                    # create figure for prob data
                    #plt.figure()
                    extent = [vis_start_ch+start_channel, vis_end_ch+start_channel,
                              prob_data_row_num, 0]
                    plt.imshow(cur_prob_data, extent=extent, aspect='auto', cmap=colormap)
                    plt.colorbar()
                    title_str = 'Prob results for -> Model: {0}, Act:{1}'.format(model_id, cur_act)
                    plt.xlabel("Channels")
                    plt.ylabel("Time index")
                    plt.title(title_str)
                    prob_data_img_name = raw_data_file_name + f"-prob_model{model_id}_{cur_act}.png"
                    prob_data_img_save_path = os.path.join(img_results_folder_path, prob_data_img_name)
                    # save prob data figure.
                    plt.savefig(prob_data_img_save_path)
                    #fig = px.imshow(cur_prob_data)
                    #fig.show()
                    # create figure for norm power
                    plt.figure()
                    extent = [vis_start_ch+start_channel, vis_end_ch+start_channel,
                              cur_norm_power.shape[0], 0]
                    plt.imshow(cur_norm_power, extent=extent, aspect='auto', cmap=colormap)
                    plt.colorbar()
                    plt.title('Norm Power [{}, {}] clipped'.format(min_norm_power, max_norm_power))
                    plt.xlabel("Channels")
                    plt.ylabel("Time index")
                    norm_power_data_img_save_path = os.path.join(img_results_folder_path,
                                                                 raw_data_file_name + "-norm_power.png")
                    # save norm power data figure
                    plt.savefig(norm_power_data_img_save_path)

                    # calculate and visualize act count
                    n_diff_prob = len(cur_prob_threshes)
                    for prob_idx in range(n_diff_prob):
                        cur_prob_thresh = cur_prob_threshes[prob_idx]
                        prob_thresh_passing = (cur_prob_data > cur_prob_thresh) * 1  # bool to 1 and 0
                        norm_power_thresh_passing = (cur_norm_power > cur_norm_power_thresh) * 1
                        power_prob_anded = (prob_thresh_passing[0::, :] & norm_power_thresh_passing[3:-3:, :]).astype(int)
                        act_counts = ndimage.convolve(power_prob_anded, cur_kernel)

                        plt.figure()
                        extent = [vis_start_ch + start_channel, vis_end_ch + start_channel,
                                  power_prob_anded.shape[0], 0]
                        plt.imshow(act_counts, extent=extent, aspect='auto', cmap=colormap)
                        plt.colorbar()
                        plt.title(title_str+', Activity counts')
                        plt.xlabel("Channels")
                        plt.ylabel("Time index")
                        act_count_img_save_path = os.path.join(img_results_folder_path,
                                                               raw_data_file_name + "-act_count.png")
                        plt.savefig(act_count_img_save_path)


                    plt.show()
                    if im_show_off:
                        plt.close("all")
                    print('cur activity ' + cur_act + ' {}/{}'.format(act_idx + 1, len(acts_to_run)))

                print('cur data: ' + raw_data_file_name + ', data progress: {0}/{1}'.format(data_idx+1, len(data_set)))


    if not is_any_data_analyzed:
        messages.warning(request, message="Cannot found power-prob value to visualise.")
        return HttpResponseRedirect("/")

    return HttpResponseRedirect("/")



def visualize_spectrogram(request, test_set_pk):

    # get selected data's hashes
    selected_data_hash_list = request.session['selected_data_hash_list']
    if not selected_data_hash_list: # if user do not select any data
        messages.warning(request, message="Please select data")
        return HttpResponseRedirect('/')

    # read vis start and vis and channels
    vis_start_channels = request.session['start_channels']
    vis_end_channels = request.session['end_channels']

    # get test set
    test_set = models.Testset.objects.get(pk=test_set_pk).__dict__
    # get data set
    data_set = test_set["data_set"]
    results_path = test_set["results_path"]
    colormap = plt.get_cmap('jet')
    img_save_path = os.path.join(results_path, "spectrogram_images")
    file_io.create_folder(img_save_path)

    for data_doc in data_set:
        if data_doc['bin_file_hash'] in selected_data_hash_list:
            # read specifications about data.
            raw_data_path = data_doc["data_full_path"]
            start_channel = data_doc["start_channel"]
            end_channel = data_doc["end_channel"]
            channel_num = data_doc["channel_num"]
            activity_channel = data_doc["activity_channel"]
            raw_data_file_name = data_doc["file_name"]
            sampling_rate = data_doc["sampling_rate"]
            time_start_idx = 0

            if sampling_rate is None:
                sampling_rate = 2000
            else:
                sampling_rate = 2000

            time_end_idx = 5 * 60 * 60 * sampling_rate # 5 hours
            # read channels to vis.

            if vis_start_channels[data_doc["bin_file_hash"]] == "" or vis_start_channels[data_doc["bin_file_hash"]].isdigit() == False or int(vis_start_channels[data_doc["bin_file_hash"]])<0:
                vis_start_ch = data_doc["start_channel"]
            else:
                #  if start channel didnt given.
                vis_start_ch = int(vis_start_channels[data_doc["bin_file_hash"]])

            if vis_end_channels[data_doc["bin_file_hash"]] == "" or vis_end_channels[data_doc["bin_file_hash"]].isdigit() == False or int(vis_end_channels[data_doc["bin_file_hash"]])>5150:
                vis_end_ch = data_doc["end_channel"]
            else:
                #  if end channel didnt given.
                vis_end_ch = int(vis_end_channels[data_doc["bin_file_hash"]])

            if vis_end_ch < vis_start_ch:
                # set default start and end channels
                vis_start_ch = data_doc["start_channel"]
                vis_end_ch = data_doc["end_channel"]


            spec_chs = np.arange(vis_start_ch, vis_end_ch+1)
            spec_chs_red = spec_chs[np.where(spec_chs < channel_num)]


            cur_chunk = das_util.read_raw_data(raw_data_path, spec_chs_red[0], spec_chs_red[-1]+1, time_start_idx,
                                               time_end_idx, channel_num)


            for cur_spec_idx, cur_spec_ch in enumerate(spec_chs_red):
                cur_ch_in_chunk = cur_spec_ch - spec_chs_red[0]
                cur_ch_data = cur_chunk[::, cur_ch_in_chunk]
                f, t, Sxx = signal.spectrogram(cur_ch_data, fs=sampling_rate, noverlap=80, nfft=400)
                Sxx_log = 10 * np.log10(Sxx + 1e-6)
                plt.figure()
                plt.pcolormesh(t, f, Sxx_log, cmap=colormap, shading='auto')
                plt.colorbar()
                plt.ylabel('Frequency [Hz]')
                plt.xlabel('Time [sec]')
                plt.title('Spectrogram ch: ' + str(cur_spec_ch+start_channel))
                path_to_save = os.path.join(img_save_path, raw_data_file_name+f"_ch{cur_spec_ch+start_channel}_spec.png")
                plt.savefig(path_to_save)
                print('cur data ch: {}, {}/{}'.format(cur_spec_ch, cur_spec_idx + 1, len(spec_chs_red)))
            plt.show()

            print('cur data file name: ' + raw_data_file_name)
            print('-'*50)

    return HttpResponseRedirect("/")


def visualise_rawdata(request, pk):
    if request.method == "POST":
        try:
            channel_to_vis = int(request.POST.get("ChannelToVis")) #get channel to visualise
        except ValueError:
            # if input is not an integer
            return HttpResponseRedirect(f'{pk}') # return back to the same page with same pk
        # get raw data path
        data_doc = models.Records.objects.get(pk=pk).__dict__
        file_name = data_doc['file_name']
        raw_data_path = data_doc['data_full_path']
        channel_num = data_doc['channel_num']
        start_channel = data_doc["start_channel"]
        end_channel = data_doc["end_channel"]
        sampling_rate = data_doc['sampling_rate']
        if channel_to_vis > end_channel or channel_to_vis < start_channel:
            return HttpResponseRedirect(f'{pk}') # return back to the same page with same pk
        if sampling_rate is None:
            sampling_rate = 2000
        raw_data = das_util.read_raw_data(file_path=raw_data_path, channel_end=channel_num, channel_num=channel_num)

        data_to_vis = raw_data[::, channel_to_vis]

        # plot the signal and the specrogram
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Raw Data", "Spectrogram for Ch: "+str(channel_to_vis)))
        # add trace for signal plot
        fig.add_trace(go.Scatter(x=np.arange(len(data_to_vis)), y=data_to_vis,
                                mode='lines', name='lines'), row=1, col=1)
        # add axes titles
        fig.update_xaxes(title_text="Time Sample", row=1, col=1)
        fig.update_yaxes(title_text="Amplitude", row=1, col=1)

        # add trace for the spectrogram
        f, t, Sxx = signal.spectrogram(data_to_vis, fs=sampling_rate, noverlap=80, nfft=400)

        Sxx_log = 10 * np.log10(Sxx + 1e-6)
        fig.add_trace(go.Heatmap(x = t, y = f, z = Sxx_log, colorscale ='Jet'), row=1, col=2)
        fig.update_xaxes(title_text="Time Sample", row=1, col=1)
        fig.update_yaxes(title_text="Amplitude", row=1, col=1)

        # add axes titles
        fig.update_xaxes(title_text="Time", row=1, col=2)
        fig.update_yaxes(title_text="Frequency", row=1, col=2)
        # update figure
        fig.update_layout(height=700, width=1000, title_text="Plots for Ch: "+str(channel_to_vis))

        # plotly graph to html
        graph = fig.to_html(full_html=False, default_height=700, default_width=1000)
        return render(request, 'analyze/ask_channel_number.html', {'graph': graph, 'pk':pk, 'f_name':file_name, 'start_ch':start_channel, 'end_ch':end_channel})

    else:
        data_doc = models.Records.objects.get(pk=pk).__dict__
        file_name = data_doc['file_name']
        start_channel = data_doc["start_channel"]
        end_channel = data_doc["end_channel"]
        return render(request, 'analyze/ask_channel_number.html', {'pk':pk, 'f_name':file_name, 'start_ch':start_channel, 'end_ch':end_channel})
