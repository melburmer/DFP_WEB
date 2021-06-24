import django_filters
from . import models
from django import forms


class DateInput(forms.DateInput):
    input_type = 'date'

class RecordFilter(django_filters.FilterSet):
    distance_to_fo = django_filters.CharFilter(field_name='distance_to_fo', lookup_expr='icontains', label='Distance to fo')
    time_of_day =django_filters.ChoiceFilter(choices=[('morning','morning'),('noon','noon'),
    ('evening','evening'),('night','night')])

    insertion_date__gt = django_filters.DateFilter(field_name='insertion_date', lookup_expr='gt', widget=DateInput(attrs={'class': 'datepicker'}))
    insertion_date__lt = django_filters.DateFilter(field_name='insertion_date', lookup_expr='lt', widget=DateInput(attrs={'class': 'datepicker'}))


    record_date__gt = django_filters.DateFilter(field_name='record_date', lookup_expr='gt', widget=DateInput(attrs={'class': 'datepicker'}))
    record_date__lt = django_filters.DateFilter(field_name='record_date', lookup_expr='lt', widget=DateInput(attrs={'class': 'datepicker'}))

    class Meta:
        model = models.Records
        fields = ['fo_use_case', 'midas_version', 'project', 'region', 'territory',
        'record_type', 'activity', 'activity_channel', 'soil_type',
        'sensor_id', 'record_label', 'channel_num','record_length_in_sec']
