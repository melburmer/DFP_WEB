from django.conf.urls import url
from . import views

app_name = "analyze"


urlpatterns = [
    url(r'create_testset/$', views.CreateTestset.as_view(), name='create_testset'),
    url(r'^select_subset_filter$', views.select_subset_filter, name="select_subset_filter"),
    url(r'^select_subset$', views.RecordSelectSubset.as_view(), name="select_subset"),
    url(r'^analyze_testset', views.AnalyzeTestSet.as_view(), name="analyze_testset")
]
