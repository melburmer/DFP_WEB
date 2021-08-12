
from django.conf.urls import url
from . import views

app_name = 'filesystem'

urlpatterns = [
    url(r'add_use_case/$', views.AddUseCase.as_view(), name='add_use_case'),
    url(r'add_midas_version/$', views.AddMidasVersion.as_view(), name='add_midas_version'),
    url(r'add_project/$', views.AddProject.as_view(), name='add_project'),
    url(r'add_region/$', views.AddRegion.as_view(), name='add_region'),
    url(r'add_record_type/$', views.AddRecordType.as_view(), name='add_record_type'),
    url(r'add_act/$', views.AddAct.as_view(), name='add_act'),

]
