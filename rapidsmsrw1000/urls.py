from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.conf.urls.defaults import *
from rapidsms.backends.kannel.views import KannelBackendView
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^account/', include('django.contrib.auth.urls')),
    # RapidSMS core URLs
    #(r'^accounts/', include('rapidsms.urls.login_logout')),
    url(r'^$',    'rapidsmsrw1000.apps.webapp.views.home' ),
    url(r'^home/$', 'rapidsmsrw1000.apps.webapp.views.dashboard', name='rapidsms-dashboard'),
    url(r'^accounts/login/$', "rapidsmsrw1000.apps.webapp.views.login", name='rapidsms-login'),
    url(r'^accounts/logout/$', "rapidsmsrw1000.apps.webapp.views.logout", name='rapidsms-logout'),
    # RapidSMS contrib app URLs
    #(r'^export/', include('rapidsms.contrib.export.urls')),
    url(r'^httptester/$',
        'rapidsmsrw1000.apps.httptester.views.generate_identity',
        {'backend_name': 'message_tester'}, name='httptester-index'),
    (r'^httptester/', include('rapidsmsrw1000.apps.httptester.urls')),
    #(r'^locations/', include('rapidsms.contrib.locations.urls')),
    (r'^messagelog/', include('rapidsmsrw1000.apps.messagelog.urls')),
    (r'^messaging/', include('rapidsms.contrib.messaging.urls')),
    #(r'^registration/', include('rapidsms.contrib.registration.urls')),
    #(r'^scheduler/', include('rapidsms.contrib.scheduler.urls')),
    (r'^ubuzima/', include('rapidsmsrw1000.apps.ubuzima.urls')),
    #(r'^reporters/', include('rapidsmsrw1000.apps.reporters.urls')),
    (r'^chws/', include('rapidsmsrw1000.apps.chws.urls')),
    (r'^ambulances/', include('rapidsmsrw1000.apps.ambulances.urls')),
    (r'^rhea/', include('rapidsmsrw1000.apps.api.rhea.urls')),

    url(r"^backend/kannel-smpp/$",
        KannelBackendView.as_view(backend_name="kannel-smpp")),

) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
