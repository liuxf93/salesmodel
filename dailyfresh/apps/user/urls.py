from django.conf.urls import url
from apps.user import views

urlpatterns = [
    url(r'^register/$', views.RegisterView.as_view(),name='register'),
    url(r'^active/(?P<token>.*)', views.ActiveView.as_view(), name='active'),  # 注册激活
    url(r'^login/$', views.LoginView.as_view(),name='login'),
]