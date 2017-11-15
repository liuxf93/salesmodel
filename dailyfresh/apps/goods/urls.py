from django.conf.urls import url
from apps.goods import views

urlpatterns = [
    url('^index/$', views.index,name='index'),
]