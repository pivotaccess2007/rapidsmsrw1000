#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.core import management
from django.db import connection
from rapidsmsrw1000.apps.chws.models import *
from xlrd import open_workbook ,cellname,XL_CELL_NUMBER,XLRDError
import datetime
from django.utils import timezone
from rapidsmsrw1000.apps.reporters import models as old_registry
from random import randint

def build_locations():
    try:
        create_nation()
        import_provinces()
        import_districts()
        import_sectors()
        import_cells()
        import_villages()
        import_facilities()
        
        return True
    except Exception, e:
        print e
        return False
    
def create_nation(name = "Rwanda", code = '00'):
    try:
        nation = Nation(name = name, code = code)
        nation.save()
        return True
    except Exception:
        return False

def import_location(filepath, sheetname, startrow, maxrow, coderow, namerow):
    #print filepath
    #print sheetname
    #print startrow
    #print maxrow
    #print coderow 
    #print namerow
    book = open_workbook(filepath)
    sheet = book.sheet_by_name(sheetname)
    #print sheet.name,sheet.nrows
    #print sheet.cell(startrow,coderow-1).value,sheet.cell(startrow,namerow-1).value
    #print sheet.cell(maxrow-1,coderow-1).value,sheet.cell(maxrow-1,namerow-1).value
    ans = []
    for row_index in range(sheet.nrows):
        if row_index < 1: continue
        #print sheet.cell(row_index,coderow-1).value, sheet.cell(row_index,namerow-1).value
        code = sheet.cell(row_index,coderow-1).value
        name = sheet.cell(row_index,namerow-1).value
        try:
            ans.append({'code' : code, 'name' : name})
        except: continue

    return ans

def import_provinces(filepath = "rapidsmsrw1000/apps/chws/xls/locations.xls", sheetname = "PROVINCES", startrow = 1, maxrow = 416, coderow = 1, namerow = 2):
    locs = []
    cnt = import_location(filepath, sheetname, startrow, maxrow, coderow, namerow)
    for c in cnt:
        try:
            code , name = c['code'], c['name']
            nation   = Nation.objects.get(code = "00")
            province = Province( code = code , name = name , nation = nation)
            province.save()
        except Exception ,e:
            locs.append({'code' : c['code'], 'name': c['name'], 'error': e})            
            continue
    return locs


def import_districts(filepath = "rapidsmsrw1000/apps/chws/xls/locations.xls", sheetname = "DISTRICTS", startrow = 1, maxrow = 416, coderow = 1, namerow = 2):
    locs = []
    cnt = import_location(filepath, sheetname, startrow, maxrow, coderow, namerow)
    for c in cnt:
        try:
            code , name = c['code'], c['name']
            province = Province.objects.get( code = code [0:len(code)-2] )
            district = District( code = code , name = name , province = province , nation = province.nation)
            district.save()
        except Exception ,e:
            locs.append({'code' : c['code'], 'name': c['name'], 'error': e})            
            continue
    return locs


def import_sectors(filepath = "rapidsmsrw1000/apps/chws/xls/locations.xls", sheetname = "SECTORS", startrow = 1, maxrow = 416, coderow = 1, namerow = 2):
    locs = []
    cnt = import_location(filepath, sheetname, startrow, maxrow, coderow, namerow)
    for c in cnt:
        try:
            code , name = c['code'], c['name']
            district = District.objects.get( code = code [0:len(code)-2] )
            sector = Sector( code = code , name = name , district = district , province = district.province, nation = district.nation)
            sector.save()
        except Exception ,e:
            locs.append({'code' : c['code'], 'name': c['name'], 'error': e})            
            continue
    return locs


def import_cells(filepath = "rapidsmsrw1000/apps/chws/xls/locations.xls", sheetname = "CELLS", startrow = 1, maxrow = 2222, coderow = 1, namerow = 2):
    locs = []
    cnt = import_location(filepath, sheetname, startrow, maxrow, coderow, namerow)
    for c in cnt:
        try:
            code , name = c['code'], c['name']
            sector = Sector.objects.get( code = code [0:len(code)-2] )
            cell = Cell( code = code , name = name , sector = sector , district = sector.district, province = sector.province, nation = sector.nation)
            cell.save()
        except Exception ,e:
            locs.append({'code' : c['code'], 'name': c['name'], 'error': e})            
            continue
    return locs

def import_villages(filepath = "rapidsmsrw1000/apps/chws/xls/locations.xls", sheetname = "VILLAGES", startrow = 1, maxrow = 14584, coderow = 1, namerow = 2):
    locs = []
    cnt = import_location(filepath, sheetname, startrow, maxrow, coderow, namerow)
    for c in cnt:
        try:
            code , name = c['code'], c['name']
            cell = Cell.objects.get( code = code [0:len(code)-2] )
            village = Village( code = code , name = name , cell = cell, sector = cell.sector, district = cell.district, province = cell.province, nation = cell.nation)
            village.save()
        except Exception, e:
            locs.append({'code' : c['code'], 'name': c['name'], 'error': e})            
            continue
    return locs


def import_facilities(filepath = "rapidsmsrw1000/apps/chws/xls/facilities.xls", sheetname = "FACILITIES", startrow = 1, maxrow = 616, codecol = 1, typecol = 2, namecol = 3, prvccol = 4, prvncol = 5, dstccol = 6, dstncol = 7, sctncol = 8, latcol = 9, longcol = 10, popcol = 11, popycol = 12):
    locs = []
    book = open_workbook(filepath)
    sheet = book.sheet_by_name(sheetname)
    i = j=0
    for row_index in range(sheet.nrows):
        if row_index < 1: continue
        try:
            #print sheet.cell(row_index,coderow-1).value, sheet.cell(row_index,namerow-1).value
            code     = str(int(float(sheet.cell(row_index,codecol-1).value)))
            name     = sheet.cell(row_index,namecol-1).value
            type     = sheet.cell(row_index,typecol-1).value
            nation   = Nation.objects.get (code = '00')
            province = Province.objects.get(code = sheet.cell(row_index,prvccol-1).value)
            district = District.objects.get(code = sheet.cell(row_index,dstccol-1).value )
            sector   = None
            
            try:
                sector   = Sector.objects.get( district = district, name__in = [ sheet.cell(row_index,sctncol-1).value , sheet.cell(row_index,sctncol-1).value.lower(), sheet.cell(row_index,sctncol-1).value.upper()] )
            except Exception, e:    pass
            
            checks = ["Hopital", "Hopital".lower(), "Hopital".upper(), "Hospital", "Hospital".lower(), "Hospital".upper()]
            
            facility = HealthCentre( code = code , name = name , sector = sector, district = district, province = province, nation = nation)
            
            for c in checks:
                if c in type:
                    facility = Hospital( code = code , name = name , sector = sector, district = district, province = province, nation = nation)
                    break
                else:   continue
            
            facility.save()
        except Exception, e:
            locs.append({'error': e})            
            continue
    return locs

def update_cells_villages(filepath = "rapidsmsrw1000/apps/chws/xls/minaloc.xls", sheetname = "GeographicAreas"):
    book = open_workbook(filepath)
    sheet = book.sheet_by_name(sheetname)
    c_n = v_n = 0
    c_codes = v_codes = []
    for row_index in range(sheet.nrows):
        if row_index < 1: continue   
        try:
            cell_code = sheet.cell(row_index,8).value
            cell_name = sheet.cell(row_index,9).value
            village_code = sheet.cell(row_index,10).value
            village_name = sheet.cell(row_index,11).value
            try:    cell = Cell.objects.get(code = cell_code)
            except Cell.DoesNotExist, e:
                try:
                    sector = Sector.objects.get(code = cell_code[0:len(cell_code)-2])
                    cell = Cell(code = cell_code , name = cell_name , sector = sector , district = sector.district, \
                                province = sector.province, nation = sector.nation).save()
                except: c_n = c_n + 1; c_codes.append(cell_code)
            try:    village = Village.objects.get(code = village_code)
            except Village.DoesNotExist, e:
                try:
                    cell = Cell.objects.get(code = village_code[0:len(village_code)-2])
                    cell = Village(code = village_code , name = village_name , cell = cell, sector = cell.sector, \
                                    district = cell.district, province = cell.province, nation = cell.nation).save()
                except: v_n = v_n + 1; v_codes.appende(village_code)
        except Exception, e:
            print e
            pass
    print "Cell: %d, Village: %d, \ncell_codes: %s\nvillage_codes: %s" % (c_n, v_n, c_codes, v_codes)

def import_supervisors(filepath = "rapidsmsrw1000/apps/chws/xls/supervisors.xls", sheetname = "supervisors"):
    book = open_workbook(filepath)
    sheet = book.sheet_by_name(sheetname)
    
    for row_index in range(sheet.nrows):
        if row_index < 1: continue   
        try:
            names = sheet.cell(row_index,0).value
            dob = sheet.cell(row_index,1).value
            area = sheet.cell(row_index,2).value
            area_level = sheet.cell(row_index,3).value
            telephone = sheet.cell(row_index,4).value
            email = sheet.cell(row_index,5).value
            district = sheet.cell(row_index,6).value
            try:
                district = District.objects.filter(name__icontains = district)[0]
                if area_level.upper().strip() == 'HC':
                    loc = HealthCentre.objects.filter(name__icontains = area, district = district)[0]
                    sup, created = Supervisor.objects.get_or_create(telephone = parse_phone_number(telephone), health_centre = loc)
                elif area_level.upper().strip() == 'HOSPITAL':
                    loc = Hospital.objects.filter(name__icontains = area, district = district)[0]
                    sup, created = Supervisor.objects.get_or_create(telephone = parse_phone_number(telephone), hospital = loc)
                if sup.random_nid is None:  sup.random_nid = "%s%s" % ( sup.telephone[3:] , str(random_with_N_digits(6)))
                sup.names = names
                sup.dob = get_date(dob)
                sup.area_level = area_level.upper().strip()
                sup.sector = loc.sector
                sup.district = loc.district
                sup.province = loc.province
                sup.nation = loc.nation
                #sup.telephone  = parse_phone_number(telephone)
                sup.email = email
                #print sup, loc
                #print loc, district, parse_phone_number(telephone), email
                if sup.health_centre is None:
                    if sup.hospital is None:
                        sup.delete()
                else:
                    sup.save()
                    sup_old_reg(sup)
            except Exception, e:
                #print e, area
                pass
            #print "\nNames : %s\n DOB : %s\n Health Centre : %s\n Hospital : %s\n Telephone : %s\n Email: %s\n District : %s\n"\
                 #% (sup.names,sup.dob,sup.health_centre,sup.hospital,sup.telephone,sup.email,sup.district)
        except Exception, e:
            #print e
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

def get_date(date_of_birth):
    
    try:
        x       = date_of_birth.split("/")
        
        if len(x) == 3 :    date_of_birth       = datetime.date(int(x[2]),int(x[1]),int(x[0]))
        elif len(x) == 1:   date_of_birth       = datetime.date(int(x[0]),01,01)                                        
    except:
        try:
            x = int(float(date_of_birth))
            if x: date_of_birth = datetime.date(x,01,01)  
        except:   date_of_birth = datetime.date.today() - datetime.timedelta(days = 7665)
    return date_of_birth

def sup_old_reg(sup):
    if sup.random_nid is None:  sup.random_nid = "%s%s" % ( sup.telephone[3:] , str(random_with_N_digits(6)))
    sup.save()
    try:
        old_reporter = get_reporter(sup.random_nid)
        
        if sup.health_centre:   old_reporter.location = old_registry.Location.objects.get(code = fosa_to_code(sup.health_centre.code))
        elif sup.hospital:  old_reporter.location = old_registry.Location.objects.get(code = fosa_to_code(sup.hospital.code))
          
        old_reporter.groups.add(old_registry.ReporterGroup.objects.get(title='Supervisor'))
        old_reporter.groups.remove(old_registry.ReporterGroup.objects.get(title='CHW'))
        
        if sup.village: old_reporter.village = sup.village.name
        else:   old_reporter.village = "Village Ntizwi" 
        old_reporter.language = "rw"
        old_reporter.save()
        
        old_connection = get_connection(sup.telephone, reporter = old_reporter)
        
        #print old_connection
    except Exception, e:
        #print e
        pass

def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

def get_reporter(national_id):
    try:
        reporter = old_registry.Reporter.objects.filter(alias = national_id)[0]
        return reporter
    except Exception, e:
        try:
            reporter = old_registry.Reporter(alias = national_id)
            reporter.save()
            return reporter
            
        except Exception, e:
            return None

def get_connection(telephone_moh, reporter = None):
    
    try:
        connection = old_registry.PersistantConnection.objects.filter(identity = telephone_moh)[0]
        
        if connection.reporter: return connection
        else:  
            connection.reporter = reporter
            connection.save()
            return connection
    except Exception, e:
        try:
            if reporter.exists():
                
                backend = old_registry.PersistantBackend.objects.get(title="kannel")
                
                connection = old_registry.PersistantConnection(backend = backend, identity = telephone_moh, \
                                                                                        reporter = reporter, last_seen = timezone.localtime(timezone.now()))
                connection.save()
                return connection
            else:
                return None
        except Exception, e:
            return None
