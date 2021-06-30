from django.conf.urls import url
from . import views

app_name = "analyze"


urlpatterns = [
    url(r'deneme/$', views.AnalyzePage.as_view(), name='deneme'),
]
