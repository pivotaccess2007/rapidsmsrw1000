#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.contrib import admin
from rapidsmsrw1000.apps.chws.models import *


class SectorAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'district')
    search_fields = ('name',)

class HealthCentreAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'sector', 'district')
    search_fields = ('name',)

class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'district')
    search_fields = ('name',)

class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'province')
    search_fields = ('name',)

class CellAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'sector', 'district')
    search_fields = ('name',)

class VillageAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'cell', 'sector', 'district')
    search_fields = ('name',)



class CHWAdmin(admin.ModelAdmin):
    list_display = ('national_id', 'telephone_moh', 'village', 'health_centre')
    search_fields = ('national_id','telephone_moh',)

class RegistrationConfirmationAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'responded', 'answer')
    search_fields = ('responded',)


admin.site.register(Role)
admin.site.register(Reporter, CHWAdmin)
admin.site.register(Nation)
admin.site.register(Province)
admin.site.register(District, DistrictAdmin)
admin.site.register(Sector, SectorAdmin)
admin.site.register(Cell, CellAdmin)
admin.site.register(Village, VillageAdmin)
admin.site.register(Hospital, HospitalAdmin)
admin.site.register(HealthCentre, HealthCentreAdmin)
admin.site.register(RegistrationConfirmation, RegistrationConfirmationAdmin)
