#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from flexselect import FlexSelectWidget
from django.contrib import admin
from rapidsmsrw1000.apps.chws.models import *

import unicodecsv as csv
import xlwt
import datetime
from django.contrib.admin import util as admin_util
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse


class ProvinceWidget(FlexSelectWidget):
    trigger_fields = ['nation']

    def details(self, base_field_instance, instance):
        pass

    def queryset(self, instance):
        nation = instance.nation
        return Province.objects.filter(nation=nation)

    def empty_choices_text(self, instance):
        return "Please update the nation field"

class DistrictWidget(FlexSelectWidget):
    trigger_fields = ['province']

    def details(self, base_field_instance, instance):    
        pass

    def queryset(self, instance):
        province = instance.province
        return District.objects.filter(province=province)

    def empty_choices_text(self, instance):
        return "Please update the province field"

class SectorWidget(FlexSelectWidget):
    trigger_fields = ['district']

    def details(self, base_field_instance, instance):    
        pass

    def queryset(self, instance):
        district = instance.district
        return Sector.objects.filter(district=district)

    def empty_choices_text(self, instance):
        return "Please update the district field"

class HealthCentreWidget(FlexSelectWidget):
    trigger_fields = ['district']

    def details(self, base_field_instance, instance):    
        pass

    def queryset(self, instance):
        district = instance.district
        return HealthCentre.objects.filter(district=district)

    def empty_choices_text(self, instance):
        return "Please update the Health Centre field"

class HospitalWidget(FlexSelectWidget):
    trigger_fields = ['district']

    def details(self, base_field_instance, instance):    
        pass

    def queryset(self, instance):
        district = instance.district
        return Hospital.objects.filter(district=district)

    def empty_choices_text(self, instance):
        return "Please update the referral hospital field"

class CellWidget(FlexSelectWidget):
    trigger_fields = ['sector']

    def details(self, base_field_instance, instance):    
        pass

    def queryset(self, instance):
        sector = instance.sector
        return Cell.objects.filter(sector=sector)

    def empty_choices_text(self, instance):
        return "Please update the sector field"

class VillageWidget(FlexSelectWidget):
    trigger_fields = ['cell']

    def details(self, base_field_instance, instance):    
        pass

    def queryset(self, instance):
        cell = instance.cell
        return Village.objects.filter(cell=cell)

    def empty_choices_text(self, instance):
        return "Please update the cell field"


def export_model_as_csv(modeladmin, request, queryset):
    if hasattr(modeladmin, 'exportable_fields'):
        field_list = modeladmin.exportable_fields
    else:
        # Copy modeladmin.list_display to remove action_checkbox
        field_list = modeladmin.list_display[:]
        #field_list.remove('action_checkbox')

    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s-%s-export-%s.csv' % (
        __package__.lower(),
        queryset.model.__name__.lower(),
        datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S'),
    )

    writer = csv.writer(response)
    writer.writerow(
        [admin_util.label_for_field(f, queryset.model, modeladmin) for f in field_list],
    )

    for obj in queryset:
        csv_line_values = []
        for field in field_list:
            field_obj, attr, value = admin_util.lookup_field(field, obj, modeladmin)
            csv_line_values.append(value)

        writer.writerow(csv_line_values)

    return response
export_model_as_csv.short_description = _('Export to CSV')

def export_model_as_excel(modeladmin, request, queryset):
    has_name_fields = ['village', 'cell', 'sector', 'health_centre', 'referral_hospital', 'district', 'province','role']
    is_date_fields = ['date_of_birth', 'dob', 'join_date']
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
                else:   sheet.write(row, col, value)
            except Exception, e:
                try:    sheet.write(row, col, value)
                except: sheet.write(row, col, "NULL")
            col = col + 1
        row = row + 1

    workbook.save(response)
    return response

export_model_as_excel.short_description = _('Export to EXCEL')


class SectorAdmin(admin.ModelAdmin):
    actions = (export_model_as_csv,export_model_as_excel)
    list_display = ('name', 'code', 'district')
    search_fields = ('name','code',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Alters the widget displayed for the base field.
        """
        if db_field.name == "province":
            kwargs['widget'] =  ProvinceWidget(
                base_field=db_field,
                modeladmin=self,
                request=request,
            )
            kwargs['label'] = 'Province'

        if db_field.name == "district":
            kwargs['widget'] =  DistrictWidget(
                base_field=db_field,
                modeladmin=self,
                request=request,
            )
            kwargs['label'] = 'District'
        
        return super(SectorAdmin, self).formfield_for_foreignkey(db_field, 
            request, **kwargs)

class HealthCentreAdmin(admin.ModelAdmin):
    actions = (export_model_as_csv,export_model_as_excel)
    list_display = ('name', 'code', 'sector', 'district')
    search_fields = ('name','code',)

class HospitalAdmin(admin.ModelAdmin):
    actions = (export_model_as_csv,export_model_as_excel)
    list_display = ('name', 'code', 'district')
    search_fields = ('name','code',)

class DistrictAdmin(admin.ModelAdmin):
    actions = (export_model_as_csv,export_model_as_excel)
    list_display = ('name', 'code', 'province')
    search_fields = ('name','code',)


class CellAdmin(admin.ModelAdmin):
    actions = (export_model_as_csv,export_model_as_excel)
    list_display = ('name', 'code', 'sector', 'district')
    search_fields = ('name','code',)

class VillageAdmin(admin.ModelAdmin):
    actions = (export_model_as_csv,export_model_as_excel)
    list_display = ('name', 'code', 'cell', 'sector', 'district')
    search_fields = ('name','code',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Alters the widget displayed for the base field.
        """
        if db_field.name == "province":
            kwargs['widget'] =  ProvinceWidget(
                base_field=db_field,
                modeladmin=self,
                request=request,
            )
            kwargs['label'] = 'Province'

        if db_field.name == "district":
            kwargs['widget'] =  DistrictWidget(
                base_field=db_field,
                modeladmin=self,
                request=request,
            )
            kwargs['label'] = 'District'
        
        if db_field.name == "sector":
            kwargs['widget'] =  SectorWidget(
                base_field=db_field,
                modeladmin=self,
                request=request,
            )
            kwargs['label'] = 'Sector'

        if db_field.name == "cell":
            kwargs['widget'] =  CellWidget(
                base_field=db_field,
                modeladmin=self,
                request=request,
            )
            kwargs['label'] = 'Cell'
        
        return super(VillageAdmin, self).formfield_for_foreignkey(db_field, 
            request, **kwargs)


class CHWAdmin(admin.ModelAdmin):
    actions = (export_model_as_csv,export_model_as_excel)
    exportable_fields = ('surname', 'given_name', 'role', 'sex', 'education_level', 'date_of_birth', 'join_date', 'national_id', 'telephone_moh', 'village', 'cell', 'sector', 'health_centre', 'referral_hospital', 'district', 'province')
    list_display = ('surname', 'given_name', 'national_id', 'telephone_moh', 'village', 'health_centre', 'role')
    list_filter = ('is_active', 'role__name', 'deactivated')
    search_fields = ('national_id','telephone_moh', 'village__name', 'cell__name', 'sector__name', 'health_centre__name', 'referral_hospital__name', 'district__name', 'province__name')


    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Alters the widget displayed for the base field.
        """
        if db_field.name == "province":
            kwargs['widget'] =  ProvinceWidget(
                base_field=db_field,
                modeladmin=self,
                request=request,
            )
            kwargs['label'] = 'Province'

        if db_field.name == "district":
            kwargs['widget'] =  DistrictWidget(
                base_field=db_field,
                modeladmin=self,
                request=request,
            )
            kwargs['label'] = 'District'

        if db_field.name == "health_centre":
            kwargs['widget'] =  HealthCentreWidget(
                base_field=db_field,
                modeladmin=self,
                request=request,
            )
            kwargs['label'] = 'Health Centre'

        if db_field.name == "referral_hospital":
            kwargs['widget'] =  HospitalWidget(
                base_field=db_field,
                modeladmin=self,
                request=request,
            )
            kwargs['label'] = 'Referral Hospital'
        
        if db_field.name == "sector":
            kwargs['widget'] =  SectorWidget(
                base_field=db_field,
                modeladmin=self,
                request=request,
            )
            kwargs['label'] = 'Sector'

        if db_field.name == "cell":
            kwargs['widget'] =  CellWidget(
                base_field=db_field,
                modeladmin=self,
                request=request,
            )
            kwargs['label'] = 'Cell'

        if db_field.name == "village":
            kwargs['widget'] =  VillageWidget(
                base_field=db_field,
                modeladmin=self,
                request=request,
            )
            kwargs['label'] = 'Village'
        
        return super(CHWAdmin, self).formfield_for_foreignkey(db_field, 
            request, **kwargs)

class RegistrationConfirmationAdmin(admin.ModelAdmin):

    list_display = ('reporter', 'responded', 'answer')
    search_fields = ('responded','reporter__telephone_moh')

class SupervisorAdmin(admin.ModelAdmin):
    actions = (export_model_as_csv,export_model_as_excel)
    list_display = ('names', 'telephone_moh', 'dob', 'national_id', 'email', 'village', 'cell', 'sector', 'health_centre', 'referral_hospital', 'district', 'province')
    search_fields = ('telephone_moh', 'email', 'names', 'village__name', 'cell__name', 'sector__name', 'health_centre__name', 'referral_hospital__name', 'district__name', 'province__name')

class DataManagerAdmin(admin.ModelAdmin):
    actions = (export_model_as_csv,export_model_as_excel)
    list_display = ('names', 'telephone_moh', 'dob', 'national_id', 'email', 'village', 'cell', 'sector', 'health_centre', 'referral_hospital', 'district', 'province')
    search_fields = ('telephone_moh', 'email', 'names', 'village__name', 'cell__name', 'sector__name', 'health_centre__name', 'referral_hospital__name', 'district__name', 'province__name')

class FacilityStaffAdmin(admin.ModelAdmin):
    actions = (export_model_as_csv,export_model_as_excel)
    list_display = ('names', 'telephone_moh', 'dob', 'national_id', 'email', 'service', 'village', 'cell', 'sector', 'health_centre', 'referral_hospital', 'district', 'province')
    search_fields = ('telephone_moh', 'email', 'names', 'village__name', 'cell__name', 'sector__name', 'health_centre__name', 'referral_hospital__name', 'district__name', 'province__name')
    list_filter = ('service', 'district__name',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Alters the widget displayed for the base field.
        """
        if db_field.name == "province":
            kwargs['widget'] =  ProvinceWidget(
                base_field=db_field,
                modeladmin=self,
                request=request,
            )
            kwargs['label'] = 'Province'

        if db_field.name == "district":
            kwargs['widget'] =  DistrictWidget(
                base_field=db_field,
                modeladmin=self,
                request=request,
            )
            kwargs['label'] = 'District'
        
        if db_field.name == "sector":
            kwargs['widget'] =  SectorWidget(
                base_field=db_field,
                modeladmin=self,
                request=request,
            )
            kwargs['label'] = 'Sector'

        if db_field.name == "cell":
            kwargs['widget'] =  CellWidget(
                base_field=db_field,
                modeladmin=self,
                request=request,
            )
            kwargs['label'] = 'Cell'

        if db_field.name == "village":
            kwargs['widget'] =  VillageWidget(
                base_field=db_field,
                modeladmin=self,
                request=request,
            )
            kwargs['label'] = 'Village'
        
        return super(FacilityStaffAdmin, self).formfield_for_foreignkey(db_field, 
            request, **kwargs)    

class MonitorEvaluatorAdmin(admin.ModelAdmin):
    actions = (export_model_as_csv,export_model_as_excel)
    list_display = ('names', 'telephone_moh', 'dob', 'national_id', 'email', 'village', 'cell', 'sector', 'health_centre', 'referral_hospital', 'district', 'province')
    search_fields = ('telephone_moh', 'email', 'names', 'village__name', 'cell__name', 'sector__name', 'health_centre__name', 'referral_hospital__name', 'district__name', 'province__name')

class HospitalDirectorAdmin(admin.ModelAdmin):
    actions = (export_model_as_csv,export_model_as_excel)
    list_display = ('names', 'telephone_moh', 'dob', 'national_id', 'email', 'village', 'cell', 'sector', 'health_centre', 'referral_hospital', 'district', 'province')
    search_fields = ('telephone_moh', 'email', 'names', 'village__name', 'cell__name', 'sector__name', 'health_centre__name', 'referral_hospital__name', 'district__name', 'province__name')


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
admin.site.register(Supervisor, SupervisorAdmin)
admin.site.register(FacilityStaff, FacilityStaffAdmin)
admin.site.register(DataManager, DataManagerAdmin)
admin.site.register(MonitorEvaluator, MonitorEvaluatorAdmin)
admin.site.register(HospitalDirector, HospitalDirectorAdmin)


