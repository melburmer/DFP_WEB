from django.db import models
from djongo import models as djongo_model
import json
from pathlib import Path
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from utils.file_io import read_json
import datetime


# Create your models here.

# abstract model to store alarm triggered filed header in record model as embedded field

class Atheader(models.Model):
    message_type = models.IntegerField()
    unit_id = models.IntegerField()
    sensor_id = models.IntegerField()
    start_channel_number = models.IntegerField()
    end_channel_number = models.IntegerField()
    sequance_number = models.IntegerField()
    sampling_rate = models.FloatField()
    bit_depth = models.IntegerField()
    array_size = models.IntegerField()

    class Meta:
        abstract=True



#records model
dynamic_doc_path =   Path(__file__).resolve().parent.parent / 'json_files' / 'dynamic_document_values.json'
class Records(models.Model):

    def __str__(self):
        return "records model"

    # read dynamic doc to determine field choices
    dynamic_doc = read_json(dynamic_doc_path)

    FO_USE_CASE_CHOICES = list(zip(dynamic_doc["fo_use_case"], dynamic_doc["fo_use_case"]))
    MIDAS_VERSION_CHOICES = list(zip(dynamic_doc["midas_version"], dynamic_doc["midas_version"]))
    PROJECT_CHOICES = list(zip(dynamic_doc["project"], dynamic_doc["project"]))
    RECORD_TYPE_CHOICES = list(zip(dynamic_doc["record_type"], dynamic_doc["record_type"]))
    RECORD_LABEL_CHOICES = list(zip(dynamic_doc["record_label"], dynamic_doc["record_label"]))
    LINE_OR_FACILITY_CHOICES = [('line','line'), ('facility', 'facility')]
    ACT_DIRECTION_CHOICES = [('horizontal','horizontal'), ('vertical', 'vertical')]
    SOIL_TYPE_CHOICES = list(zip(dynamic_doc["soil_type"], dynamic_doc["soil_type"]))

    # define avaliable field for region , activity , act specification
    # set avaliable regions
    AVALIABLE_REGION_CHOICES = []
    for project_tuple in PROJECT_CHOICES:
        project = project_tuple[0] # select first item of the tuple
        cur_region = dynamic_doc[f'region_{project}'] # fetch region for selected project
        region_tuple_list = list(zip(cur_region, cur_region)) # crete tuple from region (choices attr need tuple)
        AVALIABLE_REGION_CHOICES = AVALIABLE_REGION_CHOICES + region_tuple_list # add it to the regions list

    # set avaliable activities
    AVALIABLE_ACT_CHOICES = []
    for fo_use_case_tuple in FO_USE_CASE_CHOICES:
        fo_use_case = fo_use_case_tuple[0]
        cur_act = dynamic_doc[f'activity_type_{fo_use_case}']
        act_tuple_list = list(zip(cur_act, cur_act))
        AVALIABLE_ACT_CHOICES = AVALIABLE_ACT_CHOICES + act_tuple_list

    # set avaliable activity_specifications
    AVALIABLE_ACTSPEC_CHOICES = []
    for act_tuple in AVALIABLE_ACT_CHOICES:
        act = act_tuple[0]
        try:
            cur_act_spec = dynamic_doc[f'activity_specification_{act}']
        except KeyError:
            continue
        act_spec_tuple_list = list(zip(cur_act_spec, cur_act_spec))
        AVALIABLE_ACTSPEC_CHOICES = AVALIABLE_ACTSPEC_CHOICES + act_spec_tuple_list

    # define fields
    is_special_data = models.BooleanField(default=False)
    file_name = models.CharField(max_length=100)
    fo_use_case = models.CharField(max_length=50, choices=FO_USE_CASE_CHOICES)
    midas_version = models.CharField(max_length=50, choices=MIDAS_VERSION_CHOICES)
    project = models.CharField(max_length=50, choices=PROJECT_CHOICES)
    region = models.CharField(max_length=50, choices=AVALIABLE_REGION_CHOICES)
    territory = models.CharField(max_length=50)
    record_type = models.CharField(max_length=50, choices=RECORD_TYPE_CHOICES)
    activity = models.CharField(max_length=50, choices=AVALIABLE_ACT_CHOICES)
    activity_channel = models.IntegerField(blank=True, validators=[MaxValueValidator(limit_value=5150), MinValueValidator(limit_value=0)])
    activity_specification = models.CharField(max_length=50, blank=True, choices=AVALIABLE_ACTSPEC_CHOICES)
    activity_direction = models.CharField(max_length=50, blank=True, choices=ACT_DIRECTION_CHOICES)
    soil_type = models.CharField(max_length=50, blank=True, choices=SOIL_TYPE_CHOICES)
    pulse_width = models.IntegerField(null=True, blank=True)
    distance_to_fo = models.CharField(max_length=50, blank=True)
    sensor_id = models.CharField(max_length=50, blank=True)
    line_or_facility = models.CharField(max_length=20, blank=True, choices=LINE_OR_FACILITY_CHOICES )
    record_label = models.CharField(max_length=50, blank=True, choices=RECORD_LABEL_CHOICES)
    insertion_date = models.DateTimeField(auto_now_add=True)
    start_channel = models.PositiveIntegerField()
    end_channel = models.PositiveIntegerField()
    channel_num = models.PositiveIntegerField()
    number_of_channels_in_one_sample = models.PositiveIntegerField()
    iter_num = models.IntegerField()
    record_size = models.BigIntegerField()
    record_length_in_sec = models.IntegerField()
    sampling_rate = models.IntegerField()
    bin_file_hash = models.CharField(max_length=100, editable=False, unique=True)
    info_file_hash = models.CharField(max_length=100, editable=False, unique=True)
    time_of_day = models.CharField(max_length=50)
    record_date = models.DateTimeField()
    record_notes = models.TextField(max_length=250, blank=True)
    at_header = djongo_model.EmbeddedField(model_container=Atheader, null=True)
    data_full_path = models.CharField(max_length=100, unique=True, default="")

    class Meta:
        ordering = ['-insertion_date']
