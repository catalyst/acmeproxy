from django.urls import path
from . import views

urlpatterns = [
    path('publish_response', views.publish_response, name='publish_response'),
    path('expire_response', views.expire_response, name='expire_response'),
    path('create_authorisation', views.create_authorisation, name='create_authorisation'),
    path('expire_authorisation', views.expire_authorisation, name='expire_authorisation'),
]
