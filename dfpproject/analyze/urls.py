from django.conf.urls import url
from . import views
from django.urls import path

app_name = "analyze"


urlpatterns = [
    url(r'create_testset/$', views.CreateTestset.as_view(), name='create_testset'),
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

]
