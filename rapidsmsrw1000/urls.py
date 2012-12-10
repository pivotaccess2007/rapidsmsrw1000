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
    url(r'^home/$', 'rapidsmsrw1000.apps.webapp.views.dashboard'),
    (r'^accounts/login/$', "rapidsmsrw1000.apps.webapp.views.login"),
    (r'^accounts/logout/$', "rapidsmsrw1000.apps.webapp.views.logout"),
    # RapidSMS contrib app URLs
    #(r'^export/', include('rapidsms.contrib.export.urls')),
    url(r'^httptester/$',
        'rapidsmsrw1000.apps.httptester.views.generate_identity',
        {'backend_name': 'message_tester'}, name='httptester-index'),
    (r'^httptester/', include('rapidsmsrw1000.apps.httptester.urls')),
    #(r'^locations/', include('rapidsms.contrib.locations.urls')),
    (r'^messagelog/', include('rapidsmsrw1000.apps.messagelog.urls')),
    (r'^messaging/', include('rapidsms.contrib.messaging.urls')),
    (r'^registration/', include('rapidsms.contrib.registration.urls')),
    (r'^scheduler/', include('rapidsms.contrib.scheduler.urls')),
    (r'^ubuzima/', include('rapidsmsrw1000.apps.ubuzima.urls')),
    (r'^reporters/', include('rapidsmsrw1000.apps.reporters.urls')),
    (r'^chws/', include('rapidsmsrw1000.apps.chws.urls')),
    (r'^logger/', include('rapidsmsrw1000.apps.logger.urls')),
     
	# FAKE SMS FROM KANNEL EXTRA...
    url(r"^backend/kannel-fake-smsc/$",
        KannelBackendView.as_view(backend_name="kannel-fake-smsc")),

	# USB MODEM...
    url(r"^backend/kannel-usb0-smsc/$",
        KannelBackendView.as_view(backend_name="kannel-usb0-smsc")),

) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
