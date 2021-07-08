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
    path('calculate_power_prob/<int:pk>', views.calculate_power_prob, name='calculate_power_prob'),
    path('calculate_roc_curves/<int:pk>', views.calculate_roc_curves, name='calculate_roc_curves'),
]
