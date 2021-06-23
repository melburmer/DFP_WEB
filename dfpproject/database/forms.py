from django.forms import ModelForm
from . import models
from django import forms


class RecordCreateForm(ModelForm):

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
        self.fields['region'].widget.attrs.update({'id':'RegionField','disabled':True})
        self.fields['activity'].widget.attrs.update({'id':'ActField','disabled':True})
        self.fields['activity_specification'].widget.attrs.update({'id':'ActSpeField','disabled':True})
        self.fields['is_special_data'].widget.attrs.update({'id':'SpecialDataField'})
        self.fields['record_type'].widget.attrs.update({'id':'RecordTypeField'})
        self.fields['remove_header'].widget.attrs.update({'id':'RemoveHeaderField'})
