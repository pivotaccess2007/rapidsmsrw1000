#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from rapidsmsrw1000.apps.ambulances import views as views

urlpatterns = patterns('',
    url(r'^$', views.ambulances),
    url(r'^alphabetically/(?P<letter>\w)$', views.ambulances_by_alphabet),
    url(r'^location/(?P<loc>\d+)$', views.ambulances_by_location),
    url(r'^driver/add$', views.ambulance_driver_add),
    url(r'^driver/delete$', views.ambulance_driver_delete),
    url(r'^add$', views.ambulance_add)
)
