#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from datetime import datetime
from rapidsmsrw1000.apps.ubuzima.models import Report
from rapidsmsrw1000.apps.ubuzima.admin import ReportAdmin
from django.contrib.admin import util as admin_util

import xlsxwriter
import cStringIO as StringIO
from django.http import HttpResponse


def export_reports_to_xlsx_in_http(reports):

    # Create a workbook and add a worksheet.
    has_name_fields = ['village', 'cell', 'sector', 'health_centre', 'referral_hospital', 'district', 'province','role', 'type', 'location', 'nation']
    is_date_fields = ['date_of_birth', 'dob', 'join_date', 'date',  'edd_date' ,  'edd_anc2_date' , \
                         'edd_anc3_date',  'edd_anc4_date' ,  'edd_pnc1_date' ,  'edd_pnc2_date' ,  'edd_pnc3_date' ,'created']

    is_person_fields = ['reporter', 'patient'] 

    sheet_name = "%s" % ( reports.model.__name__.lower(), )
    output = StringIO.StringIO()
    workbook = xlsxwriter.Workbook(output)
    sheet = workbook.add_worksheet(sheet_name)

    field_list = [f.name for f in Report._meta.fields]

    row = col = 0
    last_col = []
    for f in field_list:
        sheet.write(row , col, f.upper())
        col = col + 1

    row = row + 1
    for obj in reports:
        col = 0
        for field in field_list:
            field_obj, attr, value = admin_util.lookup_field(field, obj, ReportAdmin)

            try:
                if field in has_name_fields:  sheet.write(row, col, value.name)
                elif field in is_date_fields: 
                    try:    sheet.write_datetime(row, col, value, date_format)
                    except: sheet.write_datetime(row, col, value.date(), date_format)
                elif field in is_person_fields: sheet.write(row, col, "%s" % (value.national_id))
                else:   sheet.write(row, col, value)
                                        
            except Exception, e:
                try:    sheet.write(row, col, value)
                except: sheet.write(row, col, "NULL")
            col = col + 1
        
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
                        sheet.write_number(row,mcol, d.value)
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
       


def export_reports_to_xlsx_on_disk(reports):

    # Create a workbook and add a worksheet.
    has_name_fields = ['village', 'cell', 'sector', 'health_centre', 'referral_hospital', 'district', 'province','role', 'type', 'location', 'nation']
    is_date_fields = ['date_of_birth', 'dob', 'join_date', 'date',  'edd_date' ,  'edd_anc2_date' , \
                         'edd_anc3_date',  'edd_anc4_date' ,  'edd_pnc1_date' ,  'edd_pnc2_date' ,  'edd_pnc3_date' ,'created']

    is_person_fields = ['reporter', 'patient'] 

    sheet_name = "%s" % ( reports.model.__name__.lower(), )
    filename = "%s.xlsx" % sheet_name

    workbook = xlsxwriter.Workbook(filename)
    sheet = workbook.add_worksheet(sheet_name)
    ##DATE FORMAT
    date_format = workbook.add_format({'num_format': 'mmmm dd yyyy'})


    field_list = [f.name for f in Report._meta.fields]

    row = col = 0
    last_col = []
    for f in field_list:
        sheet.write(row , col, f.upper())
        col = col + 1

    row = row + 1
    for obj in reports:
        col = 0
        for field in field_list:
            field_obj, attr, value = admin_util.lookup_field(field, obj, ReportAdmin)

            try:
                if field in has_name_fields:  sheet.write(row, col, value.name)
                elif field in is_date_fields: 
                    try:    sheet.write_datetime(row, col, value, date_format)
                    except: sheet.write_datetime(row, col, value.date(), date_format)
                elif field in is_person_fields: sheet.write(row, col, "%s" % (value.national_id))
                else:   sheet.write(row, col, value)
                                        
            except Exception, e:
                try:    sheet.write(row, col, value)
                except: sheet.write(row, col, "NULL")
            col = col + 1
        
        details = obj.fields.all()
        #print row,col, "BEFORE"
        try:
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
                            sheet.write_number(row,mcol, d.value)
                        else:
                            sheet.write(row,mcol, d.type.description)
        
                    col = col+1
        except Exception, e:
            print e
            continue
        #print last_col
        #print row,col, "AFTER"
        row = row + 1

    workbook.close()

    return True
