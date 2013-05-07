#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from rapidsmsrw1000.apps.chws import views as views

urlpatterns = patterns('',
    url(r'^$', views.view_uploads),
    url(r'^import$', views.import_reporters_from_excell, name='import_chws'),
    url(r'^messaging$', views.group_messages, name='messaging'),
    url(r'^pendings$', views.view_pendings, name='pendings'),
    url(r'^confirms$', views.view_confirms, name='confirms'),
    url(r'^view/errors/(?P<ref>\w+)$', views.errors, name='errors'),
    url(r'^view/warnings/(?P<ref>\w+)$', views.warnings, name='warnings'),
    url(r'^view/uploads$', views.view_uploads, name='uploads'),
    #url(r'^chws/download/list$', views.download_chws_list_template),

    url(r'^asm$',             views.view_asm),
    url(r'^asm/active$',             views.view_active_reporters),
    url(r'^asm/inactive$',             views.view_inactive_reporters),
    url(r'^binome$',             views.view_binome),
    url(r'^binome/active$',             views.view_active_reporters),
    url(r'^binome/inactive$',             views.view_inactive_reporters),
    url(r'^supervisor$',             views.view_supervisor),
    url(r'^datamanager$',             views.view_datamanager),
    url(r'^facilitystaff$',             views.view_facilitystaff),
    url(r'^chwreg$',             views.chwreg),
    
    
)

