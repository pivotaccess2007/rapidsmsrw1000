#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.core import management
from django.db import connection
from rapidsmsrw1000.apps.chws.models import *
from xlrd import open_workbook ,cellname,XL_CELL_NUMBER,XLRDError

from django.utils import timezone
from rapidsms.models import *
from random import randint
from django.conf import settings
import datetime

def build_chws():
    try:
        create_backends()
        create_nation()
        import_provinces()
        import_districts()
        import_sectors()
        import_facilities()
        create_role()
        import_supervisors()
        import_cells()
        import_villages()
        update_cells_villages()
        
        
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

def create_backends():
    for b in settings.INSTALLED_BACKENDS.keys():
        try:
            backend, created = Backend.objects.get_or_create( name = b)
            backend.save()
        except Exception, e:
            pass
            return False
    return True
    

def create_role():
    try:
        asm = Role(name = 'ASM', code = "asm")
        binome = Role(name = 'Binome', code = "binome")
        asm.save()
        binome.save()
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
                    loc = HealthCentre.objects.filter(name = area, district = district)[0]
                    sup, created = Supervisor.objects.get_or_create(telephone_moh = parse_phone_number(telephone) , health_centre = loc, email = email)
                elif area_level.upper().strip() == 'HOSPITAL':
                    loc = Hospital.objects.filter(name__icontains = area, district = district)[0]
                    sup, created = Supervisor.objects.get_or_create(telephone_moh = parse_phone_number(telephone), referral_hospital = loc, email = email)
                if sup.national_id is None:  sup.national_id = "%s%s" % ( sup.telephone_moh[3:] , str(random_with_N_digits(6)))
                sup.names = names
                sup.dob = get_date(dob)
                sup.area_level = area_level.upper().strip()
                sup.sector = loc.sector
                sup.district = loc.district
                sup.province = loc.province
                sup.nation = loc.nation
                sup.language = sup.language_kinyarwanda
                sup.save()
                    
            except Exception, e:
                print e, area
                pass
            #print "\nNames : %s\n DOB : %s\n Health Centre : %s\n Hospital : %s\n Telephone : %s\n Email: %s\n District : %s\n"\
                 #% (sup.names,sup.dob,sup.health_centre,sup.hospital,sup.telephone,sup.email,sup.district)
        except Exception, e:
            #print e
            pass

def import_testers(filepath = "rapidsmsrw1000/apps/chws/xls/Testers.xls", sheetname = "testers"):

    book = open_workbook(filepath)
    sheet = book.sheet_by_name(sheetname)
    
    for row_index in range(sheet.nrows):
        if row_index < 1: continue   
        try:
            names = sheet.cell(row_index,0).value
            telephone = sheet.cell(row_index,1).value
            
            try:
                hc = HealthCentre.objects.get(name = "TEST")
                hp = Hospital.objects.get(name = "TEST")
                telephone = parse_phone_number(telephone)
                nid = "%s%s" % ( telephone[3:] , str(random_with_N_digits(6)))
                try:    tester = Reporter.objects.get(telephone_moh = telephone, health_centre = hc, referral_hospital = hp)
                except:
                    tester, created = Reporter.objects.get_or_create(telephone_moh = telephone, national_id = nid, health_centre = hc, referral_hospital = hp)

                tester.surname      = names	
                tester.role            = Role.objects.get(code = 'asm')	
                tester.sex 	        =  Reporter.sex_male	
                tester.education_level = Reporter.education_universite
                tester.date_of_birth   =	datetime.datetime.today()	
                tester.join_date		=   datetime.datetime.today()
                tester.district		=   hc.district
                tester.nation			=   hc.nation
                tester.province		=   hc.province
                tester.sector			=   Sector.objects.get(name = 'TEST')
                
                tester.cell			=	Cell.objects.get(name = 'TEST')
                tester.village		=   Village.objects.get(name = 'TEST')      
                tester.updated		    = timezone.localtime(timezone.now())
                tester.language        = Reporter.language_kinyarwanda
                
                tester.save()
                confirm, created = RegistrationConfirmation.objects.get_or_create(reporter = tester)
                confirm.save()    
            except Exception, e:
                print e
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

def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

def get_reporter(national_id, telephone_moh):
    try:
        reporter = Reporter.objects.filter(national_id = national_id , telephone_moh = telephone_moh)[0]
        return reporter
    except Exception, e:
        try:
            reporter = Reporter(national_id = national_id , telephone_moh = telephone_moh)
            reporter.save()
            return reporter
            
        except Exception, e:
            return None

def get_connections(reporter):
    connections = None
    try:
        connections = Connection.objects.filter(identity = reporter.telephone_moh)
        
    except Exception, e:
        contact, created = Contact.objects.get_or_create(name = reporter.national_id)
        if reporter.language:    contact.language = reporter.language.lower()
        else:   contact.language = 'rw'

        backends = Backend.objects.all()
        for b in backends:
            try:
                identity = reporter.telephone_moh if b.name != 'message_tester' else reporter.telephone_moh.replace('+','')
                connection, created = Connection.objects.get_or_create(contact = contact, backend = b, identity = identity)

                connection.save()
            except:
                continue
        
        contact.save()
        connections = Connection.objects.filter(contact = contact)
    return connections
    
        
def update_empty_contact_connections():
	empty_contact_connections = Connection.objects.filter(contact = None)
	reporters_with_empty_contact_connections = Reporter.objects.filter(telephone_moh__in = empty_contact_connections.values_list('identity'))
	for r in reporters_with_empty_contact_connections:
		conn = Connection.objects.get(identity = r.telephone_moh)
		conn.contact = Contact.objects.get(name = r.national_id)
		conn.save()
	return True
