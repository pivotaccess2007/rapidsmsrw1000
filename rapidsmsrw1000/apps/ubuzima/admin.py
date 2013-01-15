#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.contrib import admin
from rapidsmsrw1000.apps.ubuzima.models import *

admin.site.register(Report)
admin.site.register(ReportType)
admin.site.register(Field)
admin.site.register(Patient)
admin.site.register(ReminderType)
admin.site.register(Reminder)
admin.site.register(UserLocation)
admin.site.register(TriggeredAlert)
admin.site.register(ErrorType)
admin.site.register(ErrorNote)
admin.site.register(IndicatorCategory)
admin.site.register(HealthIndicator)

class TriggerAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'message_en')
    search_fields = ('name',)
    

class FieldTypeAdmin(admin.ModelAdmin):
    list_display = ('key', 'description', 'category')
    search_fields = ('key', 'description')

admin.site.register(TriggeredText, TriggerAdmin)
admin.site.register(FieldType, FieldTypeAdmin)


