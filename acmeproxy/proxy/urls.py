from django.urls import path

from . import views

urlpatterns = [
    path("publish_response", views.PublishResponse.as_view(), name="publish_response"),
    path("expire_response", views.ExpireResponse.as_view(), name="expire_response"),
    path(
        "create_authorisation",
        views.CreateAuthorisation.as_view(),
        name="create_authorisation",
    ),
    path(
        "expire_authorisation",
        views.ExpireAuthorisation.as_view(),
        name="expire_authorisation",
    ),
]
