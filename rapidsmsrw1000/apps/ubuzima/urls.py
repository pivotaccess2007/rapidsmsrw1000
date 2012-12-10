#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
import rapidsmsrw1000.apps.ubuzima.views as views


urlpatterns = patterns('',
    url(r'^$', views.index),
    url(r'^reporter/(?P<pk>\d+)$', views.by_reporter),
    url(r'^patient/(?P<pk>\d+)$', views.by_patient),
    url(r'^type/(?P<pk>\d+)$', views.by_type),
    url(r'^alerts$', views.view_alerts),
    url(r'^alerts/type/(?P<pk>\d+)$', views.alerts_by_type),
    url(r'^triggers$', views.triggers),
    url(r'^trigger/(?P<pk>\d+)$', views.trigger),
    url(r'^reminders$', views.view_reminders),
    url(r'^reminders/type/(?P<pk>\d+)$', views.remlog_by_type),
    url(r'^report/(?P<pk>\d+)$', views.view_report),
    url(r'^stats$', views.view_stats),
    url(r'^stats/csv$', views.view_stats_csv),
    url(r'^stats/reports/csv$', views.view_stats_reports_csv),
    url(r'^indicator/(?P<indic>\d+)/(?P<format>html|csv)$', views.view_indicator),
    url(r'^important/(?P<format>\w+)/(?P<dat>\w+)$',
        views.important_data),
    url(r'^stats/anc$',
        views.view_anc),
    url(r'^stats/anc/(?P<format>\w+)/(?P<dat>\w+)$',
        views.anc_stats),
    url(r'^stats/chihe$',views.view_chihe),
    url(r'^stats/chihe/(?P<format>\w+)/(?P<dat>\w+)$',
        views.chihe_stats),
    url(r'^stats/death$', views.view_death),
    url(r'^stats/death/(?P<format>\w+)/(?P<dat>\w+)$',
        views.death_stats),
    url(r'^stats/pregnancy$', views.view_pregnancy),
    url(r'^stats/risk/(?P<format>\w+)/(?P<dat>\w+)$',
        views.risk_stats),
    url(r'^stats/risk$',views.risk_details),
    url(r'^stats/pregnancy/(?P<format>\w+)/(?P<dat>\w+)$',
        views.pregnancy_stats),
    url(r'^location/(?P<pk>\d+)$', views.by_location),
    url(r'^locationcache$', views.shorthand_locations),
    url(r'^stats/agg$', views.agstats),
    url(r'^stats/aggcsv$', views.agstats_csv),
    url(r'^dash$', views.dashboard),
    url(r'^dash/bir$', views.birth_report),
    url(r'^dash/de$', views.death_report),
    url(r'^dash/ris$', views.risk_report),
    url(r'^dash/pre$', views.preg_report),
    url(r'^dash/admin$', views.admin_report),
    url(r'^dash/chi$', views.child_report),
    url(r'^dash/chi/(?P<pk>\d+)$', views.child_details_report),
    url(r'^dash/chart$', views.charts),
    url(r'^test/(?P<dat>\w+)$', views.tests),
    url(r'^dash/anc$', views.anc_report),
    url(r'^dash/pnc$', views.pnc_report),
    url(r'^nutrition$', views.nutrition),
    url(r'^nutrition/(?P<indic>\d+)/(?P<format>html|csv)$', views.view_nutrition),
    url(r'^newborn$', views.newborn),
    url(r'^newborn/(?P<indic>\d+)/(?P<format>html|csv)$', views.view_newborn),
   # url(r'^batchimport/', include('batchimport.urls')),

    ##Generic Views
   
    url(r'^reports$', views.ReportListView.as_view()),
)