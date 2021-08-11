from django.forms import ModelForm
from . import models
from django import forms
from django.core.exceptions import ValidationError
from pathlib import Path
from utils import params


class RecordCreateForm(ModelForm):
    sampling_rate = forms.IntegerField(label="Sampling Rate", required=False, initial=2000)
    remove_header = forms.BooleanField(label="Is Alarm Triggered file contain header?", required=False)

    class Meta:
        # select fields to show

        fields = ("is_special_data","fo_use_case", "midas_version", "project", "region", "territory", "record_type", 'activity',
                'activity_channel','activity_specification', 'activity_direction', 'soil_type', 'pulse_width', 'distance_to_fo',
                 'sensor_id', 'line_or_facility', 'record_label', 'record_notes')
        model = models.Records # set model



    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs) # call super

        # set id to fields.
        self.fields['fo_use_case'].widget.attrs.update({'id':'UsecaseField'})
        self.fields['project'].widget.attrs.update({'id':'ProjectField'})
        self.fields['region'].widget.attrs.update({'id':'RegionField'})
        self.fields['activity'].widget.attrs.update({'id':'ActField'})
        self.fields['activity_specification'].widget.attrs.update({'id':'ActSpeField'})
        self.fields['is_special_data'].widget.attrs.update({'id':'SpecialDataField'})
        self.fields['sampling_rate'].widget.attrs.update({'id':'SamplingRateField'})
        self.fields['record_type'].widget.attrs.update({'id':'RecordTypeField'})
        self.fields['remove_header'].widget.attrs.update({'id':'RemoveHeaderField'})


    def clean(self):
        super().clean()
        # check for file location reference
        is_special_data = self.cleaned_data["is_special_data"]
        fo_use_case = self.cleaned_data["fo_use_case"]
        midas_version = self.cleaned_data["midas_version"]
        project = self.cleaned_data["project"]
        region = self.cleaned_data["region"]
        record_type = self.cleaned_data["record_type"]
        activity = self.cleaned_data["activity"]

        # create file reference
        if is_special_data:
        # create reference (absolute path to the data location)
        #Note: Special data reference structure is different from normal data
            reference = Path("special_data") / fo_use_case / midas_version / record_type
        else:
            # create reference (absolute path to the data location)
            reference = Path(fo_use_case) / midas_version / project / region / record_type / activity


        path = Path(params.BASE_DIR) # init path with base dir
        file_levels = str(reference).split("\\")
        for file_level in file_levels:
            path = path / file_level
            if not path.exists():
                # current file level is wrong
                raise ValidationError(f'Path:{path} is not exist, please change "{file_level}" level')
