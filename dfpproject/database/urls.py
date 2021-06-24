from django.conf.urls import url
from . import views

app_name = 'database'

urlpatterns = [
    url(r'insert/$', views.InsertRecord.as_view(), name='insert'),
    url('ajax/load_regions/', views.load_regions, name='ajax_load_regions'),
    url('ajax/load_acts/', views.load_act_types, name='ajax_load_acts'),
    url('ajax/load_actspecs/', views.load_actspecs, name='ajax_load_actspecs'),
    url(r'^list$', views.record_list, name="filter_list"),
]
