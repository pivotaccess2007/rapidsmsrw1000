#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.conf.urls.defaults import *
import rapidsmsrw1000.apps.reporters.views as views


urlpatterns = patterns('',
    url(r'^$',             views.index),
    url(r'^inactive/csv$', views.view_inactive_reporters_csv),
    url(r'^reporter$',             views.find_reporter),
    url(r'^location/(?P<pk>\d+)$',             views.reporters_by_location),
    url(r'^inactive$',             views.view_inactive_reporters),
    url(r'^inactive/location/(?P<pk>\d+)$',             views.inactive_reporters_location),
    url(r'^inactive/sup/(?P<pk>\d+)$',             views.inactive_reporters_sup),
    url(r'^add$',         views.add_reporter,  name="add-reporter"),
    url(r'^(?P<pk>\d+)$', views.edit_reporter, name="view-reporter"),
    url(r'^errors$',      views.error_list),
    url(r'^errors/type/(?P<pk>\d+)$', views.error_list_by_type),
    url(r'^errors/csv$',      views.error_list_csv),
    url(r'^errors/type/(?P<pk>\d+)/csv$',      views.error_list_csv_by_type),
    
    url(r'^groups/$',            views.index),
    url(r'^groups/add$',         views.add_group),
    url(r'^groups/(?P<pk>\d+)$', views.edit_group),
    url(r'^active$',             views.view_active_reporters),
    url(r'^active/csv$',             views.view_active_reporters_csv),
    url(r'^import$',             views.import_reporters_from_excell,name='import_start'),
)
