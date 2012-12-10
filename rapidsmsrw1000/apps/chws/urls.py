#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from rapidsmsrw1000.apps.chws import views as views

urlpatterns = patterns('',
    url(r'^$', views.view_uploads),
    url(r'^import$', views.import_reporters_from_excell, name='import_chws'),
    url(r'^pendings$', views.view_pendings, name='pendings'),
    url(r'^confirms$', views.view_confirms, name='confirms'),
    url(r'^view/errors/(?P<ref>\w+)$', views.errors, name='errors'),
    url(r'^view/warnings/(?P<ref>\w+)$', views.warnings, name='warnings'),
    url(r'^view/uploads$', views.view_uploads, name='uploads'),
    #url(r'^chws/download/list$', views.download_chws_list_template),
    
    
)

