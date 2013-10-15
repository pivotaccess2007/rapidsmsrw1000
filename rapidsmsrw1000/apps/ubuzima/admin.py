#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.contrib import admin
from rapidsmsrw1000.apps.ubuzima.models import *

import unicodecsv as csv
import xlwt
import xlsxwriter
import cStringIO as StringIO
import datetime
from django.contrib.admin import util as admin_util
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse


def export_model_as_excel(modeladmin, request, queryset):
    has_name_fields = ['village', 'cell', 'sector', 'health_centre', 'referral_hospital', 'district', 'province','role', 'type', 'location', 'nation']
    is_date_fields = ['date_of_birth', 'dob', 'join_date', 'date',  'edd_date' ,  'edd_anc2_date' ,  'edd_anc3_date',  'edd_anc4_date' ,  'edd_pnc1_date' ,  'edd_pnc2_date' ,  'edd_pnc3_date' ,'created']
    is_person_fields = ['reporter', 'patient'] 
    workbook = xlwt.Workbook()
    sheet_name = "%s" % ( queryset.model.__name__.lower(), )
    sheet = workbook.add_sheet(sheet_name)
    if hasattr(modeladmin, 'exportable_fields'):
        field_list = modeladmin.exportable_fields
    else:
        # Copy modeladmin.list_display to remove action_checkbox
        field_list = modeladmin.list_display[:]
        #field_list.remove('action_checkbox')

    response = HttpResponse(mimetype = "application/ms-excel")
    response['Content-Disposition'] = 'attachment; filename=%s.xls' % sheet_name

    row = col = 0
    last_col = []
    for f in field_list:
        sheet.write(row , col, admin_util.label_for_field(f, queryset.model, modeladmin).upper())
        col = col + 1       

    row = row + 1
    for obj in queryset:
        excel_line_values = []
        col = 0
        for field in field_list:
            field_obj, attr, value = admin_util.lookup_field(field, obj, modeladmin)

            try:
                if field in has_name_fields:  sheet.write(row, col, value.name)
                elif field in is_date_fields: sheet.write(row, col, "%d/%d/%d" % (value.day, value.month, value.year))
                elif field in is_person_fields: sheet.write(row, col, "%s" % (value.national_id))
                else:   sheet.write(row, col, value)
                                        
            except Exception, e:
                try:    sheet.write(row, col, value)
                except: sheet.write(row, col, "NULL")
            col = col + 1
        if queryset.model.__name__ == 'Report':
            details = obj.fields.all()
            #print row,col, "BEFORE"
            if details:
                for d in details:
                    lc = [lc for lc in last_col if lc['name'] == d.type.key]
                    mcol = col
                    if lc:
                        mcol = lc[0]['index']#;print mcol,d
                        if d.type.has_value:
                            sheet.write(row,mcol, d.value)
                        else:
                            sheet.write(row,mcol, d.type.description)
                        
                    else:
                        li = [lc for lc in last_col if lc['index'] == col]
                        
                        if li:
                            mcol = last_col[len(last_col)-1]['index']+1

                        #print mcol, d 
                        last_col.append({'name': d.type.key, 'index': mcol}) 
                        sheet.write(0, mcol, d.type.key)  
                        if d.type.has_value:
                            sheet.write(row,mcol, d.value)
                        else:
                            sheet.write(row,mcol, d.type.description)
        
                    col = col+1
            #print last_col
            #print row,col, "AFTER"
        row = row + 1

    workbook.save(response)
    return response

def export_model_as_excel_xlsx(modeladmin, request, queryset):
    has_name_fields = ['village', 'cell', 'sector', 'health_centre', 'referral_hospital', 'district', 'province','role', 'type', 'location', 'nation']
    is_date_fields = ['date_of_birth', 'dob', 'join_date', 'date',  'edd_date' ,  'edd_anc2_date' ,  'edd_anc3_date',  'edd_anc4_date' ,  'edd_pnc1_date' ,  'edd_pnc2_date' ,  'edd_pnc3_date' ,'created']
    is_person_fields = ['reporter', 'patient'] 
    sheet_name = "%s" % ( queryset.model.__name__.lower(), )
    # create a workbook in memory
    output = StringIO.StringIO()
    workbook = xlsxwriter.Workbook(output)
    sheet = workbook.add_worksheet(sheet_name)
    if hasattr(modeladmin, 'exportable_fields'):
        field_list = modeladmin.exportable_fields
    else:
        # Copy modeladmin.list_display to remove action_checkbox
        field_list = modeladmin.list_display[:]
        #field_list.remove('action_checkbox')

    #response = HttpResponse(mimetype = "application/ms-excel")
    #response['Content-Disposition'] = 'attachment; filename=%s.xlsx' % sheet_name

    row = col = 0
    last_col = []
    for f in field_list:
        sheet.write(row , col, admin_util.label_for_field(f, queryset.model, modeladmin).upper())
        col = col + 1       

    row = row + 1
    for obj in queryset:
        excel_line_values = []
        col = 0
        for field in field_list:
            field_obj, attr, value = admin_util.lookup_field(field, obj, modeladmin)

            try:
                if field in has_name_fields:  sheet.write(row, col, value.name)
                elif field in is_date_fields: sheet.write(row, col, "%d/%d/%d" % (value.day, value.month, value.year))
                elif field in is_person_fields: sheet.write(row, col, "%s" % (value.national_id))
                else:   sheet.write(row, col, value)
                                        
            except Exception, e:
                try:    sheet.write(row, col, value)
                except: sheet.write(row, col, "NULL")
            col = col + 1
        if queryset.model.__name__ == 'Report':
            details = obj.fields.all()
            #print row,col, "BEFORE"
            if details:
                for d in details:
                    lc = [lc for lc in last_col if lc['name'] == d.type.key]
                    mcol = col
                    if lc:
                        mcol = lc[0]['index']#;print mcol,d
                        if d.type.has_value:
                            sheet.write(row,mcol, d.value)
                        else:
                            sheet.write(row,mcol, d.type.description)
                        
                    else:
                        li = [lc for lc in last_col if lc['index'] == col]
                        
                        if li:
                            mcol = last_col[len(last_col)-1]['index']+1

                        #print mcol, d 
                        last_col.append({'name': d.type.key, 'index': mcol}) 
                        sheet.write(0, mcol, d.type.key)  
                        if d.type.has_value:
                            sheet.write(row,mcol, d.value)
                        else:
                            sheet.write(row,mcol, d.type.description)
        
                    col = col+1
            #print last_col
            #print row,col, "AFTER"
        row = row + 1
    
    workbook.close()

    # construct response
    output.seek(0)
    response = HttpResponse(output.read(), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename=%s.xlsx" % sheet_name
    return response

export_model_as_excel_xlsx.short_description = _('Export to EXCEL 2007')

export_model_as_excel.short_description = _('Export to EXCEL 2003')

admin.site.register(ReportType)

admin.site.register(Reminder)
admin.site.register(TriggeredAlert)
admin.site.register(ErrorType)
admin.site.register(ErrorNote)
admin.site.register(Refusal)
admin.site.register(Departure)


class TriggerAdmin(admin.ModelAdmin):
    actions = (export_model_as_excel, )
    exportable_fields = ('id','name', 'description', 'destination', 'message_en', 'message_fr', 'message_kw')
    list_display = ('name', 'description', 'destination', 'message_en', 'message_fr', 'message_kw')
    search_fields = ('name',)


class ReminderAdmin(admin.ModelAdmin):
    actions = (export_model_as_excel, export_model_as_excel_xlsx,)
    exportable_fields = ('id','name','message_en', 'message_fr', 'message_kw')
    list_display = ('name', 'message_en', 'message_fr', 'message_kw')
    search_fields = ('name',)

class FieldCategoryAdmin(admin.ModelAdmin):
    actions = (export_model_as_excel, )
    exportable_fields = ('name',)
    list_display = ('name', )
    search_fields = ('name',)

class FieldTypeAdmin(admin.ModelAdmin):
    actions = (export_model_as_excel, )
    exportable_fields = ('key', 'description',)
    list_display = ('key', 'description', 'category')
    search_fields = ('key', 'description')
    list_filter = ('category',)


class ReportAdmin(admin.ModelAdmin):
    actions = (export_model_as_excel, export_model_as_excel_xlsx,)
    exportable_fields = ('id', 'reporter', 'patient', 'type', 'nation', 'province', 'district', 'location', 'sector', 'cell', 'village', 'date' ,  'edd_date' ,  'bmi_anc1' ,  'edd_anc2_date' ,  'edd_anc3_date',  'edd_anc4_date' ,  'edd_pnc1_date' ,  'edd_pnc2_date' ,  'edd_pnc3_date' ,'created')
    list_filter = ('type',)
    list_display = ('id', 'type', 'patient', 'date')


class FieldAdmin(admin.ModelAdmin):
    list_filter = ('type__category__name',)
    list_display = ('id', '__unicode__', 'report',)

class UserLocationAdmin(admin.ModelAdmin):
    list_filter = ('user',)
    list_display = ('user', 'village', 'cell', 'sector', 'health_centre', 'referral_hospital', 'district', 'province', 'nation')
    search_fields = ('user__username',)

class PatientAdmin(admin.ModelAdmin):
    actions = (export_model_as_excel, )
    exportable_fields = ('id', 'national_id', 'village', 'cell', 'sector', 'district', 'province')
    list_filter = ('province', 'district',)
    list_display = ('id', 'national_id', 'telephone', 'province', 'district', 'sector', 'cell','village',)
    search_fields = ('national_id','telephone',)

admin.site.register(TriggeredText, TriggerAdmin)
admin.site.register(FieldType, FieldTypeAdmin)
admin.site.register(FieldCategory, FieldCategoryAdmin)
admin.site.register(ReminderType, ReminderAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(Field, FieldAdmin)
admin.site.register(UserLocation, UserLocationAdmin)
admin.site.register(Patient, PatientAdmin)




