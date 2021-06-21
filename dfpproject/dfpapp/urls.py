from django.conf.urls import url
from . import views

app_name = 'dfpapp'

urlpatterns = [
    url(r'insert/$', views.InsertRecord.as_view(), name='insert')
]
