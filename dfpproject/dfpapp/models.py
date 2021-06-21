from django.db import models
import json
from pathlib import Path
from django.core.validators import MaxValueValidator, MinValueValidator
from utils.file_io import read_json
import datetime


# Create your models here.
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
    # define fields
    is_special_data = models.BooleanField(default=False)
    file_name = models.CharField(max_length=100)
    fo_use_case = models.CharField(max_length=50, choices=FO_USE_CASE_CHOICES)
    midas_version = models.CharField(max_length=50, choices=MIDAS_VERSION_CHOICES)
    project = models.CharField(max_length=50, choices=PROJECT_CHOICES)
    region = models.CharField(max_length=50, choices=())
    record_type = models.CharField(max_length=50, choices=RECORD_TYPE_CHOICES)
    activity = models.CharField(max_length=50)
    activity_channel = models.IntegerField(blank=True, validators=[MaxValueValidator(limit_value=5150), MinValueValidator(limit_value=0)])
    activity_specification = models.CharField(max_length=50, blank=True)
    activity_direction = models.CharField(max_length=50, blank=True, choices=ACT_DIRECTION_CHOICES)
    soil_type = models.CharField(max_length=50, blank=True)
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
    record_size = models.BigIntegerField()
    record_length_in_sec = models.IntegerField()
    sampling_rate = models.IntegerField()
    #bin_file_hash = models.CharField(max_length=100, editable=False, unique=True,error_messages={'unique': 'Duplicate data, Cannot insert it!'})
    #info_file_hash = models.CharField(max_length=100, editable=False, unique=True,error_messages={'unique': 'Duplicate data, Cannot insert it!'})
    time_of_day = models.CharField(max_length=50)
    record_date = models.DateTimeField()
    record_notes = models.TextField(max_length=250, blank=True)
    #data_full_path = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['-insertion_date']

    # override save method to customize save operation
    def save(self, *args, **kwargs):
        self.insertion_date = datetime.datetime.now()
        super().save(*args, **kwargs)  # call the 'real' save method
