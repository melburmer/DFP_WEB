from django.conf.urls import url
from . import views

app_name = 'database'

urlpatterns = [
    url(r'insert/$', views.InsertRecord.as_view(), name='insert'),
    url('ajax/load_regions/', views.load_regions, name='ajax_load_regions'),
    url('ajax/load_acts/', views.load_act_types, name='ajax_load_acts'),
    url('ajax/load_actspecs/', views.load_actspecs, name='ajax_load_actspecs'),
    url(r'^filter$', views.record_list, name="filter"),
    url(r'^detail/(?P<pk>\d+)$', views.RecordDetail.as_view(), name='detail'),
    url(r'^update/(?P<pk>\d+)$', views.UpdateRecord.as_view(), name='update'),
    url(r'^delete/(?P<pk>\d+)$', views.DeleteRecord.as_view(), name='delete'),
    url(r'^select_subset_filter$', views.select_subset_filter, name="select_subset_filter"),
    url(r'^select_subset$', views.RecordSelectSubset.as_view(), name="select_subset"),
    url(r'^delete_many$', views.delete_many, name="delete_selected_data"),
]
