from django.db import models
from djongo import models as djongo_model
from django.core.validators import MaxValueValidator, MinValueValidator
from database.models import Atheader, Records
# Create your models here.


class Records_Container(models.Model):

    # define fields
    is_special_data = models.BooleanField(default=False)
    file_name = models.CharField(max_length=100)
    fo_use_case = models.CharField(max_length=50)
    midas_version = models.CharField(max_length=50)
    project = models.CharField(max_length=50)
    region = models.CharField(max_length=50)
    territory = models.CharField(max_length=50, blank=True, null=True)
    record_type = models.CharField(max_length=50)
    activity = models.CharField(max_length=50)
    activity_channel = models.IntegerField(blank=True, validators=[MaxValueValidator(limit_value=5150), MinValueValidator(limit_value=0)])
    activity_specification = models.CharField(max_length=50, blank=True)
    activity_direction = models.CharField(max_length=50, blank=True)
    soil_type = models.CharField(max_length=50, blank=True)
    pulse_width = models.IntegerField(null=True, blank=True)
    distance_to_fo = models.CharField(max_length=50, blank=True)
    sensor_id = models.CharField(max_length=50, blank=True)
    line_or_facility = models.CharField(max_length=20, blank=True)
    record_label = models.CharField(max_length=50, blank=True)
    insertion_date = models.DateTimeField(auto_now_add=True)
    start_channel = models.PositiveIntegerField()
    end_channel = models.PositiveIntegerField()
    channel_num = models.PositiveIntegerField()
    number_of_channels_in_one_sample = models.PositiveIntegerField()
    iter_num = models.IntegerField()
    record_size = models.BigIntegerField()
    record_length_in_sec = models.IntegerField()
    sampling_rate = models.IntegerField(blank=True, default=2000)
    bin_file_hash = models.CharField(max_length=100, editable=False, unique=True)
    info_file_hash = models.CharField(max_length=100, editable=False, unique=True)
    time_of_day = models.CharField(max_length=50)
    record_date = models.DateTimeField()
    record_notes = models.TextField(max_length=250, blank=True, default="")
    at_header = djongo_model.EmbeddedField(model_container=Atheader, null=True)
    data_full_path = models.CharField(max_length=250, unique=True, default="")

    class Meta:
        abstract=True



class Testset(models.Model):
    test_set_name = models.CharField(max_length=50)
    models_to_run = models.CharField(max_length=100)
    acts_to_run = models.CharField(max_length=100)
    data_set = djongo_model.ArrayField(model_container=Records_Container, default="")
    results_path = models.CharField(max_length=250, unique=True, default="")
    testset_purporse = models.TextField(max_length=250, blank=True, default="")
