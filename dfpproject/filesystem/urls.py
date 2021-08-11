
from django.conf.urls import url
from . import views

app_name = 'filesystem'

urlpatterns = [
    url(r'add_use_case/$', views.AddUseCase.as_view(), name='add_use_case'),
]
