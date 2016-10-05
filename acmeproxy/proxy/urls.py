from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^dns/lookup/(?P<qname>[^/]+)/(?P<qtype>.*)$', views.lookup, name='lookup'),
    url(r'^dns/.*$', views.not_implemented, name='not_implemented'),
    url(r'^publish_response$', views.publish_response, name='publish_response'),
    url(r'^expire_response$', views.expire_response, name='expire_response'),
    url(r'^create_authorisation$', views.create_authorisation, name='create_authorisation'),
    url(r'^expire_authorisation$', views.expire_authorisation, name='expire_authorisation'),
]
