from django.forms import ModelForm
from . import models
from django import forms


class RecordCreateForm(ModelForm):

    class Meta:

        fields = ("is_special_data","fo_use_case", "midas_version", "project", "region", "record_type", 'activity',
                'activity_channel','activity_specification', 'activity_direction', 'soil_type', 'pulse_width', 'distance_to_fo',
                 'sensor_id', 'line_or_facility', 'record_label', 'record_notes')
        model = models.Records

        # give ID to form fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['project'].widget.attrs.update({'id':'ProjectField'})
        self.fields['region'].widget.attrs.update({'id':'RegionField'})
