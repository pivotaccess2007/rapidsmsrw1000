#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.core import management
from django.db import connection
from rapidsmsrw1000.apps.ambulances.models import *
from xlrd import open_workbook ,cellname,XL_CELL_NUMBER,XLRDError

from django.utils import timezone
from rapidsms.models import *
from random import randint
from django.conf import settings
import datetime


def import_ambulances(filepath = "rapidsmsrw1000/apps/ambulances/xls/ambulances.xls", sheetname = "ambulances"):
    book = open_workbook(filepath)
    sheet = book.sheet_by_name(sheetname)
    
    for row_index in range(sheet.nrows):
        if row_index < 1: continue   
        try:
            telephone = sheet.cell(row_index,1).value
            names = sheet.cell(row_index,2).value
            nid = sheet.cell(row_index,3).value
            area = sheet.cell(row_index,4).value
            
            try:
                loc = HealthCentre.objects.filter(name__icontains = area.strip())
                if loc.exists():
                    amb, created = AmbulanceDriver.objects.get_or_create(phonenumber = telephone, health_centre = loc[0], district = loc[0].district)
                    amb.identity, amb.name = nid, names
                    amb.save()
                else:
                    loc = Hospital.objects.filter(name__icontains = area.strip())
                    amb, created = AmbulanceDriver.objects.get_or_create(phonenumber = telephone, referral_hospital = loc[0], district = loc[0].district)
                    amb.identity, amb.name = nid, names
                    amb.save()
                    
            except Exception, e:
                print e, area
                pass
            
        except Exception, e:
            print e
            pass

def import_drivers(filepath = "rapidsmsrw1000/apps/ambulances/xls/drivers.xls", sheetname = "drivers"):
    book = open_workbook(filepath)
    sheet = book.sheet_by_name(sheetname)
    
    for row_index in range(sheet.nrows):
        if row_index < 1: continue   
        try:
            names = "%s %s" % (str(sheet.cell(row_index,1).value) , str(sheet.cell(row_index,2).value))
            email = sheet.cell(row_index,3).value
            telephone = parse_phone_number(sheet.cell(row_index,4).value)
            nid = "%s%s" % ( telephone[3:] , str(random_with_N_digits(6)))
            area = sheet.cell(row_index,6).value
            area_level = sheet.cell(row_index,7).value            

            try:
                loc = HealthCentre.objects.filter(name__icontains = area.strip())
                if loc.exists() and area_level.lower().strip() == 'hc':
                    amb, created = AmbulanceDriver.objects.get_or_create(phonenumber = telephone, health_centre = loc[0], district = loc[0].district)
                    amb.identity, amb.name = nid, names
                    amb.save()
                
                else:
                    loc = Hospital.objects.filter(name__icontains = area.strip())
                    amb, created = AmbulanceDriver.objects.get_or_create(phonenumber = telephone, referral_hospital = loc[0], district = loc[0].district)
                    amb.identity, amb.name = nid, names
                    amb.save()
                   
            except Exception, e:
                print e, area
                pass
            
        except Exception, e:
            print e
            pass

def parse_phone_number(number):

    number = number
    try:
        number = str(int(float(number)))
    except:
        try:
            number = str(int(number))
        except:
            try:
                number = str(number)
            except:
                    return False
    number = number.replace(" ", "")
    try:
        if type(number)!=str:
            number=str(int(number))
        if number[:3]=="+25" and len(number[3:])==10:
            number=number
        elif number[:3]=="250" and len(number[3:])==9:
            number="+"+number
        elif number[:3]=="078" and len(number[3:])==7:
            number="+25"+number
        elif number[:2]=="78" and len(number[2:])==7:
            number="+250"+number
        return number
    except: 
            return False

def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)
