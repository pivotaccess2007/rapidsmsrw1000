#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.contrib import admin
from rapidsmsrw1000.apps.ambulances.models import *


class AmbulanceDriverAdmin(admin.ModelAdmin):
    list_display = ('phonenumber','name', 'identity', 'health_centre', 'referral_hospital','district')
    search_fields = ('name','phonenumber','identity',)

class AmbulanceAdmin(admin.ModelAdmin):
    list_display = ('plates', 'health_centre', 'referral_hospital', 'drivers','district')
    search_fields = ('plates',)

admin.site.register(AmbulanceDriver, AmbulanceDriverAdmin)
admin.site.register(Ambulance, AmbulanceAdmin)
