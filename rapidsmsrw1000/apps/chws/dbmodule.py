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
from decimal import *

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

"""After modifying models by adding the following line to Province, District, Sector, Cell and Village models:
minaloc_approved = models.BooleanField(default=False)

Execute the minaloc.sql file to reflect changes in the DB

Then call the following build_minaloc_list function

"""
def build_minaloc_list(filepath = "rapidsmsrw1000/apps/chws/xls/Rwanda_Delimitation-Revised.xls", sheetname = "Delimitation", startrow = 1, maxrow = 14838,\
                             codeprv = 0, nameprv = 1, codedis = 2, namedis = 3, codesec = 4, namesec = 5, \
                            codecel = 6, namecel = 7, codevil = 8, namevil = 9):    
    
    book = open_workbook(filepath)
    sheet = book.sheet_by_name(sheetname)
    unreg_prvs = []; unreg_diss = []; unreg_secs = []; unreg_cels = []; unreg_vils = []
            
    row = startrow

    while (row < maxrow):

        ##print book, sheet, row, maxrow, sheet.cell(row, codeprv).value, sheet.cell(row, codedis).value, sheet.cell(row, codesec).value, sheet.cell(row, codecel).value, sheet.cell(row, codevil).value
        #if row == 100:   break
        try:
            codeprvv = sheet.cell(row, codeprv).value
            nameprvv = sheet.cell(row, nameprv).value
            codedisv = sheet.cell(row, codedis).value
            namedisv = sheet.cell(row, namedis).value
            codesecv = sheet.cell(row, codesec).value
            namesecv = sheet.cell(row, namesec).value
            codecelv = sheet.cell(row, codecel).value
            namecelv = sheet.cell(row, namecel).value
            codevilv = sheet.cell(row, codevil).value
            namevilv = sheet.cell(row, namevil).value

            prv = None; dis = None; sec = None; cel = None; vil = None
            nation = Nation.objects.get(name = 'Rwanda')
        
            try:
                prv = Province.objects.get(code = codeprvv)
                prv.name = nameprvv#.upper()
                prv.nation = nation
                prv.minaloc_approved = True
                prv.save()
            except Province.DoesNotExist, e:
                print e, row, codeprvv, nameprvv
                unreg_prvs.append([codeprvv, nameprvv])
                try:
                    prv = Province(code = codeprvv, name = nameprvv, nation = nation, minaloc_approved = True)
                    prv.save()
                except Exception, e:
                    print e                    
                    break
            
            try:
                dis = District.objects.get(code = codedisv, province = prv)
                dis.name = namedisv#.upper()
                dis.nation = nation
                dis.province = prv
                dis.minaloc_approved = True
                dis.save()
            except District.DoesNotExist, e:
                print e, row, codedisv, namedisv
                unreg_diss.append([codedisv, namedisv])
                try:
                    dis = District(code = codedisv, name = namedisv, nation = nation, province = prv, minaloc_approved = True)
                    dis.save()
                except Exception, e:
                    print e                    
                    break

            try:
                sec = Sector.objects.get(code = codesecv, district = dis)
                sec.name = namesecv#.upper()
                sec.nation = nation
                sec.province = prv
                sec.district = dis
                sec.minaloc_approved = True
                sec.save()
            except Sector.DoesNotExist, e:
                print e, row, codesecv, namesecv
                unreg_secs.append([codesecv, namesecv])
                try:
                    sec = Sector(code = codesecv, name = namesecv, nation = nation, province = prv, district = dis, minaloc_approved = True)
                    sec.save()
                except Exception, e:
                    print e                    
                    break

            try:
                cel = Cell.objects.get(code = codecelv, sector = sec)
                cel.name = namecelv#.upper()
                cel.nation = nation
                cel.province = prv
                cel.district = dis
                cel.sector = sec
                cel.minaloc_approved = True
                cel.save()
            except Cell.DoesNotExist, e:
                print e, row, codecelv, namecelv
                unreg_cels.append([codecelv, namecelv])
                try:
                    cel = Cell(code = codecelv, name = namecelv, nation = nation, province = prv, district = dis, sector = sec, minaloc_approved = True)
                    cel.save()
                except Exception, e:
                    print e                    
                    break

            try:
                vil = Village.objects.get(code = codevilv, cell = cel)
                vil.name = namevilv#.upper()
                vil.nation = nation
                vil.province = prv
                vil.district = dis
                vil.sector = sec
                vil.cell = cel
                vil.minaloc_approved = True
                vil.save()
            except Village.DoesNotExist, e:
                print e, row, codevilv, namevilv
                unreg_vils.append([codevilv, namevilv])
                try:
                    vil = Village(code = codevilv, name = namevilv, province = prv, district = dis, sector = sec, cell = cel, nation = nation, minaloc_approved = True)
                    vil.save()
                except Exception, e:
                    print e                    
                    break
            
            #print row, codeprvv, nameprvv, codedisv, namedisv, codesecv, namesecv, codecelv, namecelv, codevilv, namevilv
            print row, prv, dis, sec, cel, vil
            row = row + 1
        except Exception ,e:
            print e           
            continue

    print unreg_prvs, unreg_diss, unreg_secs, unreg_cels, unreg_vils
            
    return True

def clean_db_after_minaloc_list_build():

    unp = Province.objects.filter(minaloc_approved = False).exclude(name = "TEST")
    und = District.objects.filter(minaloc_approved = False).exclude(name = "TEST")
    uns = Sector.objects.filter(minaloc_approved = False).exclude(name = "TEST")
    unc = Cell.objects.filter(minaloc_approved = False).exclude(name = "TEST")
    unv = Village.objects.filter(minaloc_approved = False).exclude(name = "TEST")

    objs = []

    for v in unv:
        chws_count = v.chw_village.all().count()
        correct_village = None
        if chws_count > 0:
            try:    correct_village = Village.objects.get(name = v.name, cell = v.name, minaloc_approved = True)
            except Exception, e:
                
                try:
                    correct_village = Village.objects.get(name = v.name,sector = v.sector, minaloc_approved = True)
                except:
                    print e
                    pass

        if correct_village:
            
            for chw in v.chw_village.all(): objs.append(chw)
            for dtm in v.datamanager_set.all(): objs.append(dtm)
            for dep in v.depvillage.all(): objs.append(dep)
            for err in v.errorvillage.all(): objs.append(err)
            for fct in v.facilitystaff_set.all(): objs.append(fct)
            for fld in v.fieldvillage.all(): objs.append(fld)
            for hsd in v.hospitaldirector_set.all(): objs.append(hsd)
            for mne in v.monitorevaluator_set.all(): objs.append(mne)
            for pat in v.patvillage.all(): objs.append(pat)
            for ref in v.refusalvillage.all(): objs.append(ref)
            for rem in v.remindervillage.all(): objs.append(rem)
            for rpt in v.reportvillage.all(): objs.append(rpt)
            for sup in v.supervisor_set.all(): objs.append(sup)
            for trg in v.triggervillage.all(): objs.append(trg)
            for usr in v.uservillage.all(): objs.append(usr)
            
            for obj in objs:
                obj.village = correct_village
                obj.cell = correct_village.cell
                obj.sector = correct_village.sector
                obj.district = correct_village.district
                obj.province = correct_village.province
                obj.nation = correct_village.nation
                try:
                    obj.save()
                except Exception, e:
                    print e, v.code, v.name, correct_village.code, correct_village.name
                    continue
        
        v.delete()
        
    unp.delete()
    und.delete()
    uns.delete()
    unc.delete()
    

    return True

def migrate_chws(sector, health_centre):

    chws = Reporter.objects.filter(sector = sector)

    for chw in chws:
        objs = []
        chw.health_centre = health_centre
        chw.save()
        for rpt in chw.reportreporter.all():
            objs.append(rpt)
            for fld in rpt.fields.all(): objs.append(fld)   
        for ref in chw.refusalreporter.all(): objs.append(ref)
        for dep in chw.depmother.all(): objs.append(dep)
        for alt in chw.alertreporter.all(): objs.append(alt)
        for err in chw.erringreporter.all(): objs.append(err)
        for rem in chw.reminderreporter.all(): objs.append(rem)
        #for fld in chw.fieldreporter.all(): objs.append(fld)
                
        for obj in objs:
            obj.village = chw.village
            obj.cell = chw.cell
            obj.location = chw.health_centre
            obj.sector = chw.sector
            obj.district = chw.district
            obj.province = chw.province
            obj.nation = chw.nation
            try:
                obj.save()
            except Exception, e:
                print e, chw.given_name, chw.surname, chw.health_centre, chw.village
                continue
    return True
    

    
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

def update_cells_villages(filepath = "rapidsmsrw1000/apps/chws/xls/MINALOC SECTORS_EG.xls", sheetname = "villages"):
    book = open_workbook(filepath)
    sheet = book.sheet_by_name(sheetname)
    c_n = v_n = 0
    c_codes = v_codes = []
    for row_index in range(sheet.nrows):
        if row_index < 1: continue   
        try:
            nation_name = sheet.cell(row_index,1).value

            province_code = sheet.cell(row_index,2).value
            province_name = sheet.cell(row_index,3).value
            district_code = sheet.cell(row_index,4).value
            district_name = sheet.cell(row_index,5).value
            sector_code = sheet.cell(row_index,6).value
            sector_name = sheet.cell(row_index,7).value
            cell_code = sheet.cell(row_index,8).value
            cell_name = sheet.cell(row_index,9).value
            village_code = sheet.cell(row_index,10).value
            village_name = sheet.cell(row_index,11).value
            
            nation = Nation.objects.get(name = nation_name.strip())
            province, created = Province.objects.get_or_create(code = province_code)
            district, created = District.objects.get_or_create(code = district_code)
            sector, created = Sector.objects.get_or_create(code = sector_code)
            cell, created = Cell.objects.get_or_create(code = cell_code)
            village, created = Village.objects.get_or_create(code = village_code)

            #province.name, province.nation =  province_name.strip(), nation
            
            district.name, district.province, district.nation = district_name.strip().upper(), province, nation
            
            sector.name, sector.district, sector.province, sector.nation = sector_name.strip().upper(), district, province, nation

            cell.name, cell.sector, cell.district, cell.province, cell.nation = cell_name.strip().upper(), sector, district, province, nation

            village.name, village.cell, village.sector, village.district, village.province, village.nation = village_name.strip().upper(), cell, sector, district, province, nation

            #province.save()
            district.save()
            sector.save()
            cell.save()
            village.save()

        except Exception, e:
            print e, village_name,village_code
            pass
    #print "Cell: %d, Village: %d, \ncell_codes: %s\nvillage_codes: %s" % (c_n, v_n, c_codes, v_codes)

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

def import_datamanagers(filepath = "rapidsmsrw1000/apps/chws/xls/datamanagers.xls", sheetname = "datamanagers"):
    book = open_workbook(filepath)
    sheet = book.sheet_by_name(sheetname)
    
    for row_index in range(sheet.nrows):
        if row_index < 1: continue   
        try:
            names = "%s %s" % (str(sheet.cell(row_index,0).value), str(sheet.cell(row_index,1).value))
            email = sheet.cell(row_index,2).value
            telephone = sheet.cell(row_index,3).value
            district = sheet.cell(row_index,4).value
            hosp = sheet.cell(row_index,5).value
            hc = sheet.cell(row_index,6).value
            area_level = sheet.cell(row_index,7).value
            
            try:
                district = District.objects.filter(name = district.strip())
                hospital = Hospital.objects.filter(name__icontains = hosp.strip(), district = district)[0]
                loc = HealthCentre.objects.filter(name__icontains = hc.strip(), district = district)[0]
                
                dtm, created = DataManager.objects.get_or_create(telephone_moh = parse_phone_number(telephone), referral_hospital = hospital,\
                                                         health_centre = loc,email = email.strip(), area_level = area_level.upper().strip())

                if dtm.national_id is None:  dtm.national_id = "%s%s" % ( dtm.telephone_moh[3:] , str(random_with_N_digits(6)))
                dtm.names = names
                dtm.sector = loc.sector
                dtm.district = loc.district
                dtm.province = loc.province
                dtm.nation = loc.nation
                dtm.language = dtm.language_kinyarwanda
                dtm.save()
                    
            except Exception, e:
                print e, area
                pass
            #print "\nNames : %s\n DOB : %s\n Health Centre : %s\n Hospital : %s\n Telephone : %s\n Email: %s\n District : %s\n"\
                 #% (dtm.names,dtm.dob,dtm.health_centre,dtm.referral_hospital,dtm.telephone_moh,dtm.email,dtm.district)
        except Exception, e:
            #print e
            pass

def import_monitors_evaluators(filepath = "rapidsmsrw1000/apps/chws/xls/datamanagers.xls", sheetname = "M&E"):
    book = open_workbook(filepath)
    sheet = book.sheet_by_name(sheetname)
    
    for row_index in range(sheet.nrows):
        if row_index < 1: continue   
        try:
            names = "%s %s" % (str(sheet.cell(row_index,0).value), str(sheet.cell(row_index,1).value))
            email = sheet.cell(row_index,2).value
            telephone = sheet.cell(row_index,3).value
            district = sheet.cell(row_index,4).value
            hosp = sheet.cell(row_index,5).value
            hc = sheet.cell(row_index,6).value
            area_level = sheet.cell(row_index,7).value
            
            try:
                district = District.objects.filter(name = district.strip())
                hospital = Hospital.objects.filter(name = hosp.strip(), district = district)
                loc = HealthCentre.objects.filter(name = hc.strip(), district = district)
                
                if hospital.exists():
                    monitor, created = MonitorEvaluator.objects.get_or_create(telephone_moh = parse_phone_number(telephone), referral_hospital = hospital[0],\
                                                                                email = email.strip(), area_level = 'hd', district = district[0])    
                if loc.exists():
                    monitor, created = MonitorEvaluator.objects.get_or_create(telephone_moh = parse_phone_number(telephone), health_centre = loc[0],\
                                                                                email = email.strip(), area_level = 'hc', district = district[0])

                monitor, created = MonitorEvaluator.objects.get_or_create(telephone_moh = parse_phone_number(telephone), email = email.strip(),\
                                                                             area_level = 'ds', district = district[0])

                if monitor.national_id is None:  monitor.national_id = "%s%s" % ( monitor.telephone_moh[3:] , str(random_with_N_digits(6)))
                monitor.names = names
                monitor.district = district[0]
                monitor.province = district[0].province
                monitor.nation = district[0].nation
                monitor.language = monitor.language_kinyarwanda
                monitor.save()
                    
            except Exception, e:
                print e, area_level
                pass
            print "\nNames : %s\n DOB : %s\n Health Centre : %s\n Hospital : %s\n Telephone : %s\n Email: %s\n District : %s\n"\
                 % (monitor.names,monitor.dob,monitor.health_centre,monitor.referral_hospital,monitor.telephone_moh,monitor.email,monitor.district)
        except Exception, e:
            print e
            pass


def import_hospital_directors(filepath = "rapidsmsrw1000/apps/chws/xls/hospitaldirectors.xls", sheetname = "HD"):
    book = open_workbook(filepath)
    sheet = book.sheet_by_name(sheetname)
    
    for row_index in range(sheet.nrows):
        if row_index < 1: continue   
        try:
            names = "%s %s" % (str(sheet.cell(row_index,0).value), str(sheet.cell(row_index,1).value))
            email = sheet.cell(row_index,2).value
            telephone = sheet.cell(row_index,3).value
            district = sheet.cell(row_index,4).value
            hosp = sheet.cell(row_index,5).value
                        
            try:
                district = District.objects.filter(name = district.strip())
                hospital = Hospital.objects.filter(name__icontains = hosp.strip(), district = district);print district,hospital,district[0].province,names
                
                if hospital.exists():
                    dh, created = HospitalDirector.objects.get_or_create(telephone_moh = parse_phone_number(telephone), referral_hospital = hospital[0],\
                                                                                email = email.strip(), area_level = 'hd', district = district[0])    
            
                    if dh.national_id is None:  dh.national_id = "%s%s" % ( dh.telephone_moh[3:] , str(random_with_N_digits(6)))
                    dh.names = names
                    dh.district = district[0]
                    dh.province = district[0].province
                    dh.nation = district[0].nation
                    dh.language = dh.language_kinyarwanda
                    dh.save()
                    
            except Exception, e:
                print e
                pass 
            print "\nNames : %s\n DOB : %s\n Health Centre : %s\n Hospital : %s\n Telephone : %s\n Email: %s\n District : %s\n"\
                 % (dh.names, dh.dob, dh.health_centre, dh.referral_hospital, dh.telephone_moh, dh.email, dh.district)
        except Exception, e:
            print e
            pass

def import_facilitystaff(filepath = "rapidsmsrw1000/apps/chws/xls/facilitystaff.xls", sheetname = "facilitystaff"):
    book = open_workbook(filepath)
    sheet = book.sheet_by_name(sheetname)
    
    for row_index in range(sheet.nrows):
        if row_index < 1: continue   
        try:
            names = sheet.cell(row_index,0).value
            dob = sheet.cell(row_index,1).value
            area = sheet.cell(row_index,2).value
            area_level = sheet.cell(row_index,3).value
            service = sheet.cell(row_index,4).value
            telephone = str(Decimal(sheet.cell(row_index,5).value))
            email = sheet.cell(row_index,6).value
            district = sheet.cell(row_index,7).value

            #print names, dob, area, area_level, service, telephone, email, district
            
            try:
                district = District.objects.filter(name__icontains = district.strip())[0]
                if area_level.upper().strip() == 'HC':  loc = HealthCentre.objects.filter(name__icontains = area.strip(), district = district)[0]
                elif area_level.upper().strip() == 'HOSPITAL':  loc = Hospital.objects.filter(name__icontains = area, district = district)[0]
                telephone = parse_phone_number(telephone)
                try:
                    stf = FacilityStaff.objects.get(national_id__contains = telephone[3:])    
                except:
                    national_id = "%s%s" % ( telephone[3:] , str(random_with_N_digits(6)))
                    if area_level.upper().strip() == 'HC':
                        
                        if len(email.strip()) <= 0:
                            stf, created = FacilityStaff.objects.get_or_create(telephone_moh = telephone , health_centre = loc,
                                                        national_id = national_id)
                        else:
                            stf, created = FacilityStaff.objects.get_or_create(telephone_moh = telephone , health_centre = loc, \
                                                email = email.strip(), area_level = 'hc', national_id = national_id)
                        stf.area_level = stf.ref_health_centre
        
                    elif area_level.upper().strip() == 'HOSPITAL':
                        
                        if len(email.strip()) <= 0:
                            stf, created = FacilityStaff.objects.get_or_create(telephone_moh = telephone, referral_hospital = loc,\
                                                    national_id = national_id)
                        else:
                            stf, created = FacilityStaff.objects.get_or_create(telephone_moh = telephone, referral_hospital = loc,\
                                     email = email.strip(), area_level = 'hd', national_id = national_id) 
                        stf.area_level = stf.district_hospital

                stf.names = names
                stf.dob = get_date(dob)
                stf.sector = loc.sector
                stf.district = loc.district
                stf.province = loc.province
                stf.nation = loc.nation
                stf.language = stf.language_kinyarwanda
                stf.service = service.lower()
                
                stf.save()
                
            
                    
            except Exception, e:
                print e, row_index#, area, service, email,area_level, district, stf.service, stf.area_level
                pass
            
            print "\nNames : %s\n DOB : %s\n Health Centre : %s\n Hospital : %s\n Telephone : %s\n Email: %s\n District : %s\n"\
                 % (stf.names,stf.dob,stf.health_centre,stf.referral_hospital,stf.telephone_moh,stf.email,stf.district)
            
        except Exception, e:
            print e, row_index
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
        except:   date_of_birth = datetime.date.today() - datetime.timedelta(days = 16200)
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


def update_login(reporter_chw_object):
    from  django.contrib.auth.models import User, Permission, Group
    from rapidsmsrw1000.apps.ubuzima.models import UserLocation    

    person = reporter_chw_object

    permissions = Permission.objects.filter(codename__icontains = 'view')
    group, created = Group.objects.get_or_create(name = 'DataViewer')
    group.permissions = permissions
    group.save()
    try:    user, created = User.objects.get_or_create(username = person.email)
    except:
        user = User.objects.filter(email = person.email)
        user.delete()
        user, created = User.objects.get_or_create(username = person.email)
    user.email = person.email
    user.set_password("123")
    user.groups.add(group)
    user.save()
    
    try:    
        if person.area_level.lower() == 'hc':
            user_location = UserLocation.objects.filter(user = user)
            user_location.delete()
            user_location = UserLocation.objects.create(user = user)
            user_location.health_centre = person.health_centre
            loc = person.health_centre
            user_location.save()
        elif person.area_level.lower() == 'hd':
            user_location = UserLocation.objects.filter(user = user)
            user_location.delete()
            user_location = UserLocation.objects.create(user = user)
            user_location.district = person.district
            loc = person.district
            user_location.save()

        message = "Dear %s, you are registered in RapidSMS Rwanda to track the first 1000 days of life. \
                    Your username is %s and default password is %s, please feel free to change it at http://rapidsms.moh.gov.rw:5000/account/password_reset/ .\
                    Login in www.rapidsms.moh.gov.rw:5000 website to access data from %s %s, where you are registered now." % \
                    (person.names, user.username, "123", loc, person.area_level)

        #print message
        ensure_connections_exists(person, message)
        user.email_user(subject = "RapidSMS RWANDA - Registration Confirmation", message = message, from_email = "unicef@rapidsms.moh.gov.rw")
    except Exception, e:
        print e
        pass

    return True

def ensure_connections_exists(reporter_chw_object, message):
    reporter = reporter_chw_object
    conns = reporter.get_connections()
    if conns:
            from rapidsmsrw1000.apps.ubuzima.smser import Smser
            Smser().send_message_via_kannel(reporter.connection().identity, message)
        
    else:   return False
    

