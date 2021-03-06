from django.conf.urls import url
from . import views
from django.urls import path

app_name = "analyze"


urlpatterns = [
    url(r'create_testset/$', views.CreateTestset.as_view(), name='create_testset'),
    url(r'edit_testset/$', views.EditTestset.as_view(), name='edit_testset'),
    url(r'update_testset/(?P<pk>\d+)$', views.UpdateTestset.as_view(), name='update_testset'),
    url(r'list_testset/$', views.ListTestset.as_view(), name='list_testset'),
    url(r'detail_testset/(?P<pk>\d+)$', views.DetailTestset.as_view(), name='detail_testset'),
    url(r'add_data_to_testset_form/(?P<pk>\d+)$', views.add_data_to_testset_form, name='add_data_to_testset_form'),
    url(r'add_data_to_testset/(?P<pk>\d+)$', views.add_data_to_testset, name='add_data_to_testset'),
    url(r'delete_data_from_testset/(?P<pk>\d+)$', views.delete_data_from_testset, name='delete_data_from_testset'),
    url(r'^select_subset_filter$', views.select_subset_filter, name="select_subset_filter"),
    url(r'^select_subset$', views.RecordSelectSubset.as_view(), name="select_subset"),
    url(r'^select_testset', views.SelectTestSet.as_view(), name="select_testset"),
    url(r'^analyze_testset', views.AnalyzeTestSet.as_view(), name="analyze_testset"),
    path('route_selected_testset_subset/<int:caller_id>/<int:test_set_pk>', views.route_selected_testset_subset, name='route_selected_testset_subset'),
    path('calculate_power_prob/<int:pk>', views.calculate_power_prob, name='calculate_power_prob'),
    path('calculate_roc_curves/<int:pk>', views.calculate_roc_curves, name='calculate_roc_curves'),
    path('select_test_data_subset/<int:caller_id>/<int:pk>', views.select_test_data_subset, name='select_test_data_subset'),
    path('visualize_power_prob/<int:test_set_pk>', views.visualize_power_prob, name='visualize_power_prob'),
    path('visualize_spectrogram/<int:test_set_pk>', views.visualize_spectrogram, name='visualize_spectrogram'),
    url(r'^visualise_rawdata/(?P<pk>\d+)$', views.visualise_rawdata, name='visualise_rawdata'),


]
