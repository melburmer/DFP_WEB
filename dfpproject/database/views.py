from django.shortcuts import render
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView, ListView
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from . import forms
from utils.file_io import read_json
from utils import params, das_util, file_io
from helper_modules.hashing import hash_file
from pathlib import Path
from django.http import HttpResponseRedirect
from django.contrib import messages
from . import filters
from . import models
import os
import datetime
import shutil


# Create your views here.

dynamic_doc_path =   Path(__file__).resolve().parent.parent / 'json_files' / 'dynamic_document_values.json'
base_dir = params.BASE_DIR


class InsertRecord(SuccessMessageMixin, CreateView):
    form_class = forms.RecordCreateForm
    success_url = reverse_lazy('home')
    template_name = 'database/record_form.html'
    success_message = "Record is created successfully!"

    def form_valid(self, form):

        # ask bin file path
        source_bin_file_path = file_io.ask_file_path(extension='bin')

        if source_bin_file_path == "": # check if user select any bin file.
            messages.warning(self.request, message='Please select bin file.')
            return HttpResponseRedirect('/') # return back to home page with warning


        # get record object.
        self.object = form.save(commit=False)
        """ ___proprocessing of record___ """
        if self.object.is_special_data:
        # create reference (absolute path to the data location)
        #Note: Special data reference structure is different from normal data
            reference = Path("special_data") / self.object.fo_use_case / self.object.midas_version / self.object.record_type
        else:
            # create reference (absolute path to the data location)
            reference = Path(self.object.fo_use_case) / self.object.midas_version / self.object.project / self.object.region / self.object.record_type / self.object.activity

        if self.object.record_type == "on_demand":
            if os.path.exists(source_bin_file_path + ".info"):
                # if bin and info files are stored in the same file.
                source_info_file_path = source_bin_file_path + ".info"
            else:
                # ask info file path
                source_info_file_path = file_io.ask_file_path(extension='info')

                if source_info_file_path == "": # check if user select any info file.
                    messages.warning(self.request, message='Please select info file.')
                    return HttpResponseRedirect('/') # return back to home page with warning
        else: # handle alarm triggered record
            # if remove header is true, remove header from alarm triggered file.
            # access remove_header form element with cleaned data because it isn't model field.
            if form.cleaned_data['remove_header']:
                dict_info, dict_header = das_util.extract_at_header(source_bin_file_path)
                source_info_file_path = source_bin_file_path + '.info'
                # save info to file
                file_io.save_to_json(dict_info, source_info_file_path)
                # set header
                self.object.at_header = dict_header
            else:
                # if user want to insert at file whose header has already extracted.
                # ask info file path
                source_info_file_path = file_io.ask_file_path(extension='info')

                if source_info_file_path == "": # check if user select any info file.
                    messages.warning(self.request, message='Please select info file.')
                    return HttpResponseRedirect('/') # return back to home page with warning

        # read start and end channel from info file  and calculate iter_num
        try:
            start_channel, channel_num = file_io.get_num_channel_from_info(source_info_file_path)
        except Exception as e:
                messages.error(self.request, message=e)
                return HttpResponseRedirect('/') # return back to home page with error
        end_channel = start_channel + channel_num - 1
        if start_channel > end_channel:
                messages.error(self.request, message="Start channel cannot be greater than end channel")
                return HttpResponseRedirect('/') # return back to home page with error

        # if activity channel didn't specified
        if self.object.activity_channel is None:
            self.object.activity_channel = start_channel + round(channel_num/2) # take central channel of the record

        # read info content
        info_dict = file_io.read_json(source_info_file_path)  # read relevant info file
        number_of_channels_in_one_sample = int(info_dict["number_of_channels_in_one_sample"])
        record_notes = info_dict["record_notes"]
        # get file size
        record_size = os.path.getsize(source_bin_file_path)  # returns byte
        # get iteration number from size of bin file.
        iter_num = record_size / (2 * number_of_channels_in_one_sample * 400)
        self.object.iter_num = iter_num
        # sampling Rate
        sampling_rate = form.cleaned_data['sampling_rate']
        if sampling_rate is None: # if user didnt input sampling rate.
            sampling_rate = 2000
        # calculate record length
        record_length = round(record_size/(2*channel_num*sampling_rate))  # seconds

        # set model values
        self.object.start_channel = start_channel
        self.object.end_channel = end_channel
        self.object.channel_num = channel_num
        self.object.number_of_channels_in_one_sample = number_of_channels_in_one_sample
        self.object.record_size = record_size
        self.object.record_length_in_sec = record_length
        self.object.sampling_rate = sampling_rate

        # make sure user use 'meter' in distance_to_fo attribute
        try:
            int(self.object.distance_to_fo)
            self.object.distance_to_fo = str(self.object.distance_to_fo) + 'm'
        except ValueError:
            # it means user use string
            pass

        # create hash for selected bin and info file
        self.object.info_file_hash = hash_file(source_info_file_path)
        self.object.bin_file_hash = hash_file(source_bin_file_path)

        # extract date from selected bin file
        # if record date key is exist in the relevant info file
        if "record_date_time" in info_dict.keys():
            record_date_str = info_dict["record_date_time"]
            date = record_date_str.split("--")[0]
            time = record_date_str.split("--")[1]
            year, month, day = list(map(lambda x: int(x), date.split("-")))  # extracts year/month/day from date string to create datetime object
            hour, minute, second = list(map(lambda x: int(x), time.split("-")))  # extracts hour, minute, second
            record_date_timestamp = datetime.datetime(year, month, day, hour, minute, second)

        else: # split by a special convention for bin file to get the record date
            record_date = source_bin_file_path.split("--")
            # record_date[1] -> year/month/day , record_date[2]-> hour/minute/second
            record_date_str = record_date[1] + "--" + record_date[2].split(".")[0]  # extract record date part
            year, month, day = list(map(lambda x: int(x), record_date[1].split("-")))  # extracts year/month/day from date string to create datetime object
            hour, minute, second = list(map(lambda x: int(x), record_date[2].split(".")[0].split("-")))  # extracts hour, minute, second
            record_date_timestamp = datetime.datetime(year, month, day, hour, minute, second)

        self.object.time_of_day = das_util.find_time_of_day(hour)
        self.object.record_date = record_date_timestamp
        if self.object.record_notes is None:
            # if user didn't write any note, use info file's record note section.
            self.object.record_notes = record_notes
        destination_file_path = Path(params.BASE_DIR) / reference

        """ handle file naming convention """
        if self.object.soil_type is None and self.object.distance_to_fo is None:
            destination_file_name = "ch" + str(self.object.activity_channel) + "--" + record_date_str + ".bin"

        elif (self.object.soil_type is None) and (not self.object.distance_to_fo is None):
            destination_file_name = self.object.distance_to_fo + "_" + "ch" + str(self.object.activity_channel) + "--" + record_date_str + ".bin"

        elif (not self.object.soil_type is None) and (self.object.distance_to_fo is None):
            destination_file_name = self.object.soil_type + "_" + "ch" + str(self.object.activity_channel) + "--" + record_date_str + ".bin"

        else:
            destination_file_name = self.object.soil_type + "_" + self.object.distance_to_fo + "_" + "ch" + str(self.object.activity_channel) + "--" + record_date_str + ".bin"

        if not self.object.territory is None:
            destination_file_name = f"{self.object.territory}_" + destination_file_name

        self.object.file_name = destination_file_name
        self.object.data_full_path = destination_file_path / destination_file_name
        destination_full_path = destination_file_path / destination_file_name

        if not os.path.exists(destination_full_path):
            shutil.move(src=source_bin_file_path, dst=destination_full_path)
            # move info file into file hierarchy
            shutil.move(src=source_info_file_path, dst=os.path.join(destination_file_path, destination_file_name+".info"))
        else:
            messages.error(self.request, message="A file found that contain same full_path with the destination path: " + str(destination_full_path))
            return HttpResponseRedirect('/') # return back to home page with error

        """ ___save record___ """
        self.object.save()
        print("Saved successfully!!")

        # call super
        return super().form_valid(form)


class InsertManyRecord(SuccessMessageMixin, CreateView):

    form_class = forms.RecordCreateForm
    success_url = reverse_lazy('home')
    template_name = 'database/record_form.html'
    success_message = "Records are created successfully!"

    def form_valid(self, form):
        is_any_record_inserted = False # will be used to check if any record is inserted

        # ask directory path
        source_directory_path = file_io.ask_directory()
        if source_directory_path == "": # check if user select a directory.
            messages.warning(self.request, message='Please select a directory.')
            return HttpResponseRedirect('/') # return back to home page with warning

        for file_name in os.listdir(source_directory_path):
            # check if file is bin file or not
            if not (".bin" in file_name and ".info" not in file_name):
                continue

            is_any_record_inserted = True
            source_bin_file_path = os.path.join(source_directory_path, file_name)

            # get object
            self.object = form.save(commit=False)

            if self.object.is_special_data:
            # create reference (absolute path to the data location)
            #Note: Special data reference structure is different from normal data
                reference = Path("special_data") / self.object.fo_use_case / self.object.midas_version / self.object.record_type
            else:
                # create reference (absolute path to the data location)
                reference = Path(self.object.fo_use_case) / self.object.midas_version / self.object.project / self.object.region / self.object.record_type / self.object.activity

            if self.object.record_type == "on_demand":
                if os.path.exists(source_bin_file_path + ".info"):
                    # if bin and info files are stored in the same file.
                    source_info_file_path = source_bin_file_path + ".info"
                else:
                    # ask info file path
                    source_info_file_path = file_io.ask_file_path(extension='info', msg=f'for {file_name}')

                    if source_info_file_path == "": # check if user select any info file.
                        messages.warning(self.request, message='Please select an info file.')
                        return HttpResponseRedirect('/') # return back to home page with warning
            else: # handle alarm triggered record
                # if remove header is true, remove header from alarm triggered file.
                # access remove_header form element with cleaned data because it isn't model field.
                if form.cleaned_data['remove_header']:
                    dict_info, dict_header = das_util.extract_at_header(source_bin_file_path)
                    source_info_file_path = source_bin_file_path + '.info'
                    # save info to file
                    file_io.save_to_json(dict_info, source_info_file_path)
                    # set header
                    self.object.at_header = dict_header
                else:
                    # if user want to insert at file whose header has already extracted.
                    # ask info file path
                    source_info_file_path = file_io.ask_file_path(extension='info')

                    if source_info_file_path == "": # check if user select any info file.
                        messages.warning(self.request, message='Please select info file.')
                        return HttpResponseRedirect('/') # return back to home page with warning

            # read start and end channel from info file  and calculate iter_num
            try:
                start_channel, channel_num = file_io.get_num_channel_from_info(source_info_file_path)
            except Exception as e:
                    messages.error(self.request, message=e)
                    return HttpResponseRedirect('/') # return back to home page with error
            end_channel = start_channel + channel_num - 1
            if start_channel > end_channel:
                    messages.error(self.request, message="Start channel cannot be greater than end channel")
                    return HttpResponseRedirect('/') # return back to home page with error

            # if activity channel didn't specified
            if self.object.activity_channel is None:
                self.object.activity_channel = start_channel + round(channel_num/2) # take central channel of the record

            # read info content
            info_dict = file_io.read_json(source_info_file_path)  # read relevant info file
            number_of_channels_in_one_sample = int(info_dict["number_of_channels_in_one_sample"])
            record_notes = info_dict["record_notes"]
            # get file size
            record_size = os.path.getsize(source_bin_file_path)  # returns byte
            # get iteration number from size of bin file.
            iter_num = record_size / (2 * number_of_channels_in_one_sample * 400)
            self.object.iter_num = iter_num
            # sampling Rate
            sampling_rate = form.cleaned_data['sampling_rate']
            if sampling_rate is None: # if user didnt input sampling rate.
                sampling_rate = 2000
            # calculate record length
            record_length = round(record_size/(2*channel_num*sampling_rate))  # seconds

            # set model values
            self.object.start_channel = start_channel
            self.object.end_channel = end_channel
            self.object.channel_num = channel_num
            self.object.number_of_channels_in_one_sample = number_of_channels_in_one_sample
            self.object.record_size = record_size
            self.object.record_length_in_sec = record_length
            self.object.sampling_rate = sampling_rate

            # make sure user use 'meter' in distance_to_fo attribute
            try:
                int(self.object.distance_to_fo)
                self.object.distance_to_fo = str(self.object.distance_to_fo) + 'm'
            except ValueError:
                # it means user use string
                pass

            # create hash for selected bin and info file
            self.object.info_file_hash = hash_file(source_info_file_path)
            self.object.bin_file_hash = hash_file(source_bin_file_path)

            # extract date from selected bin file
            # if record date key is exist in the relevant info file
            if "record_date_time" in info_dict.keys():
                record_date_str = info_dict["record_date_time"]
                date = record_date_str.split("--")[0]
                time = record_date_str.split("--")[1]
                year, month, day = list(map(lambda x: int(x), date.split("-")))  # extracts year/month/day from date string to create datetime object
                hour, minute, second = list(map(lambda x: int(x), time.split("-")))  # extracts hour, minute, second
                record_date_timestamp = datetime.datetime(year, month, day, hour, minute, second)

            else: # split by a special convention for bin file to get the record date
                record_date = source_bin_file_path.split("--")
                # record_date[1] -> year/month/day , record_date[2]-> hour/minute/second
                record_date_str = record_date[1] + "--" + record_date[2].split(".")[0]  # extract record date part
                year, month, day = list(map(lambda x: int(x), record_date[1].split("-")))  # extracts year/month/day from date string to create datetime object
                hour, minute, second = list(map(lambda x: int(x), record_date[2].split(".")[0].split("-")))  # extracts hour, minute, second
                record_date_timestamp = datetime.datetime(year, month, day, hour, minute, second)

            self.object.time_of_day = das_util.find_time_of_day(hour)
            self.object.record_date = record_date_timestamp
            if self.object.record_notes is None:
                # if user didn't write any note, use info file's record note section.
                self.object.record_notes = record_notes
            destination_file_path = Path(params.BASE_DIR) / reference

            """ handle file naming convention """
            if self.object.soil_type is None and self.object.distance_to_fo is None:
                destination_file_name = "ch" + str(self.object.activity_channel) + "--" + record_date_str + ".bin"

            elif (self.object.soil_type is None) and (not self.object.distance_to_fo is None):
                destination_file_name = self.object.distance_to_fo + "_" + "ch" + str(self.object.activity_channel) + "--" + record_date_str + ".bin"

            elif (not self.object.soil_type is None) and (self.object.distance_to_fo is None):
                destination_file_name = self.object.soil_type + "_" + "ch" + str(self.object.activity_channel) + "--" + record_date_str + ".bin"

            else:
                destination_file_name = self.object.soil_type + "_" + self.object.distance_to_fo + "_" + "ch" + str(self.object.activity_channel) + "--" + record_date_str + ".bin"

            if not self.object.territory is None:
                destination_file_name = f"{self.object.territory}_" + destination_file_name

            self.object.file_name = destination_file_name
            self.object.data_full_path = destination_file_path / destination_file_name
            destination_full_path = destination_file_path / destination_file_name

            if not os.path.exists(destination_full_path):
                shutil.move(src=source_bin_file_path, dst=destination_full_path)
                # move info file into file hierarchy
                shutil.move(src=source_info_file_path, dst=os.path.join(destination_file_path, destination_file_name+".info"))
            else:
                messages.error(self.request, message="A file found that contain same full_path with the destination path: " + str(destination_full_path))
                return HttpResponseRedirect('/') # return back to home page with error

            """ ___save record___ """
            self.object.pk = None # primary key is set to None to save new object for each bin file.
            self.object.save()
            print("Saved successfully!!")

        # call super
        if is_any_record_inserted:
            return super().form_valid(form)
        else:
            messages.warning(self.request, "This directory do not contain any bin file.")
            return HttpResponseRedirect('/')



class UpdateRecord(SuccessMessageMixin, UpdateView):
    form_class = forms.RecordCreateForm
    success_url = reverse_lazy('home')
    success_message = "Record is updated successfully!"
    template_name = 'database/record_form.html'
    model = models.Records

    def form_valid(self, form):
        # get object record_date
        self.object = form.save(commit=False)
        # source bin file path = data full path
        source_bin_file_path = self.object.data_full_path
        source_info_file_path = source_bin_file_path + ".info"

        # recalculate reference
        if self.object.is_special_data:
        # create reference (absolute path to the data location)
        #Note: Special data reference structure is different from normal data
            reference = Path("special_data") / self.object.fo_use_case / self.object.midas_version / self.object.record_type
        else:
            # create reference (absolute path to the data location)
            reference = Path(self.object.fo_use_case) / self.object.midas_version / self.object.project / self.object.region / self.object.record_type / self.object.activity

        if self.object.record_type == "alarm_triggered":
            if form.cleaned_data['remove_header']:
                dict_info, dict_header = das_util.extract_at_header(source_bin_file_path)
                # save info to file
                file_io.save_to_json(dict_info, source_info_file_path)
                # set header
                self.object.at_header = dict_header

        # read start and end channel from info file  and calculate iter_num
        try:
            start_channel, channel_num = file_io.get_num_channel_from_info(source_info_file_path)
        except Exception as e:
                messages.error(self.request, message=e)
                return HttpResponseRedirect('/') # return back to home page with error
        end_channel = start_channel + channel_num - 1
        if start_channel > end_channel:
                messages.error(self.request, message="Start channel cannot be greater than end channel")
                return HttpResponseRedirect('/') # return back to home page with error

        # if activity channel didn't specified
        if self.object.activity_channel is None:
            self.object.activity_channel = start_channel + round(channel_num/2) # take central channel of the record

        # read info content
        info_dict = file_io.read_json(source_info_file_path)  # read relevant info file
        number_of_channels_in_one_sample = int(info_dict["number_of_channels_in_one_sample"])
        record_notes = info_dict["record_notes"]
        # get file size
        record_size = os.path.getsize(source_bin_file_path)  # returns byte
        # get iteration number from size of bin file.
        iter_num = record_size / (2 * number_of_channels_in_one_sample * 400)
        self.object.iter_num = iter_num
        # sampling Rate
        sampling_rate = form.cleaned_data['sampling_rate']
        if sampling_rate is None: # if user didnt input sampling rate.
            sampling_rate = 2000
        # calculate record length
        record_length = round(record_size/(2*channel_num*sampling_rate))  # seconds

        # set model values
        self.object.start_channel = start_channel
        self.object.end_channel = end_channel
        self.object.channel_num = channel_num
        self.object.number_of_channels_in_one_sample = number_of_channels_in_one_sample
        self.object.record_size = record_size
        self.object.record_length_in_sec = record_length
        self.object.sampling_rate = sampling_rate

        # make sure user use 'meter' in distance_to_fo attribute
        try:
            int(self.object.distance_to_fo)
            self.object.distance_to_fo = str(self.object.distance_to_fo) + 'm'
        except ValueError:
            # it means user use string
            pass

        # extract date from selected bin file
        # if record date key is exist in the relevant info file
        if "record_date_time" in info_dict.keys():
            record_date_str = info_dict["record_date_time"]
            date = record_date_str.split("--")[0]
            time = record_date_str.split("--")[1]
            year, month, day = list(map(lambda x: int(x), date.split("-")))  # extracts year/month/day from date string to create datetime object
            hour, minute, second = list(map(lambda x: int(x), time.split("-")))  # extracts hour, minute, second
            record_date_timestamp = datetime.datetime(year, month, day, hour, minute, second)

        else: # split by a special convention for bin file to get the record date
            record_date = source_bin_file_path.split("--")
            # record_date[1] -> year/month/day , record_date[2]-> hour/minute/second
            record_date_str = record_date[1] + "--" + record_date[2].split(".")[0]  # extract record date part
            year, month, day = list(map(lambda x: int(x), record_date[1].split("-")))  # extracts year/month/day from date string to create datetime object
            hour, minute, second = list(map(lambda x: int(x), record_date[2].split(".")[0].split("-")))  # extracts hour, minute, second
            record_date_timestamp = datetime.datetime(year, month, day, hour, minute, second)

        if self.object.record_notes is None:
            # if user didn't write any note, use info file's record note section.
            self.object.record_notes = record_notes

        destination_file_path = Path(params.BASE_DIR) / reference

        """ handle file naming convention """
        if self.object.soil_type is None and self.object.distance_to_fo is None:
            destination_file_name = "ch" + str(self.object.activity_channel) + "--" + record_date_str + ".bin"

        elif (self.object.soil_type is None) and (not self.object.distance_to_fo is None):
            destination_file_name = self.object.distance_to_fo + "_" + "ch" + str(self.object.activity_channel) + "--" + record_date_str + ".bin"

        elif (not self.object.soil_type is None) and (self.object.distance_to_fo is None):
            destination_file_name = self.object.soil_type + "_" + "ch" + str(self.object.activity_channel) + "--" + record_date_str + ".bin"

        else:
            destination_file_name = self.object.soil_type + "_" + self.object.distance_to_fo + "_" + "ch" + str(self.object.activity_channel) + "--" + record_date_str + ".bin"

        if not self.object.territory is None:
            destination_file_name = f"{self.object.territory}_" + destination_file_name

        self.object.file_name = destination_file_name
        self.object.data_full_path = destination_file_path / destination_file_name
        destination_full_path = destination_file_path / destination_file_name

        if not source_bin_file_path == destination_full_path:
            try:
                shutil.move(src=source_bin_file_path, dst=destination_full_path)
                # move info file into file hierarchy
                shutil.move(src=source_info_file_path, dst=os.path.join(destination_file_path, destination_file_name+".info"))
            except FileNotFoundError as e:
                messages.error(self.request, message=e)
                return HttpResponseRedirect('/')

        return super().form_valid(form)


class RecordDetail(DetailView):
    context_object_name = 'record_detail'
    model = models.Records
    template_name = "database/record_detail.html"


class DeleteRecord(SuccessMessageMixin, DeleteView):
    model = models.Records
    success_url = reverse_lazy('home')
    success_message = "Record is deleted successfully!"

    def delete(self, *args, **kwargs):
        self.object = self.get_object()

        # delete record from file hierarchy
        bin_file_path = self.object.data_full_path
        info_file_path = bin_file_path + ".info"
        os.remove(bin_file_path)
        os.remove(info_file_path)
        return super().delete(*args, **kwargs)


class RecordSelectSubset(ListView):
    model = models.Records
    template_name = "database/record_subset_list.html"
    context_object_name = "records"

    def get_queryset(self):
        qs = self.model.objects.all()
        filtered_list = filters.RecordFilter(self.request.GET, queryset=qs)
        return filtered_list.qs



# delete selected data
def delete_many(request):
    pk_to_delete = request.POST.getlist('checks')
    if not pk_to_delete:
        # if empty list
        messages.warning(request, message="Please select data to delete")
        return HttpResponseRedirect('/')
    for pk in pk_to_delete:
        try:
            record_obj = models.Records.objects.get(pk=pk)
            # delete raw database
            rawdata_path_to_delete = record_obj.data_full_path
            info_path_to_delete = rawdata_path_to_delete + ".info"
            os.remove(rawdata_path_to_delete)
            os.remove(info_path_to_delete)
            # delete record object
            record_obj.delete()

        except Exception as e:
            messages.error(request, message=e)
            return HttpResponseRedirect('/')

    messages.success(request, message="Selected data are successfuly deleted.")
    return HttpResponseRedirect('/')


# return filter to the record_filter.html (filter result and filter form are shown in same page.)
def record_list(request):
    f = filters.RecordFilter(request.GET, queryset=models.Records.objects.all())
    return render(request, 'database/record_filter.html', {'filter':f})


# return filter to the record_select_filter.html (filter result and filter form are shown in difference page.)
def select_subset_filter(request):
    f = filters.RecordFilter(request.GET, queryset=models.Records.objects.all())
    return render(request, 'database/record_subset_filter.html', {'filter':f})


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

def export_data(request):
    data_to_export_pk = request.POST.getlist('data_to_export')
    # ask destination directory to the user.
    dest_directory_path = file_io.ask_directory()
    if dest_directory_path == "": # check if user select a directory.
        messages.warning(request, message='Please select a destination directory.')
        return HttpResponseRedirect('/') # return back to home page with warning

    if data_to_export_pk:
        for pk in data_to_export_pk:
            raw_data_full_path = models.Records.objects.get(pk=pk).data_full_path # get raw data path
            info_data_full_path = raw_data_full_path + ".info" # info file path
            try:
                # copy data
                shutil.copy(src=raw_data_full_path, dst=dest_directory_path)
                shutil.copy(src=info_data_full_path, dst=dest_directory_path)
            except Exception as e:
                messages.error(request, message=e)
                return HttpResponseRedirect('/') # return back to home page with warning

        messages.success(request, message="Filtered data are successfully exported.")
        return HttpResponseRedirect('/')
    return HttpResponseRedirect('/')
