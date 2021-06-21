from django.forms import ModelForm
from . import models


class RecordCreateForm(ModelForm):
    class Meta:

        fields = ("is_special_data","fo_use_case", "midas_version", "project", "region", "record_type", 'activity',
                'activity_channel','activity_specification', 'activity_direction', 'soil_type', 'pulse_width', 'distance_to_fo',
                 'sensor_id', 'line_or_facility', 'record_label', 'record_notes')
        model = models.Records
