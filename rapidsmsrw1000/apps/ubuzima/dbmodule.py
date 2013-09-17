#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.core import management
from django.db import connection
from rapidsmsrw1000.apps.ubuzima.models import *
from rapidsmsrw1000.apps.chws.models import *
import glob
from xlrd import open_workbook ,cellname,XL_CELL_NUMBER,XLRDError
import csv
from rapidsmsrw1000.apps.ubuzima.smser import Smser
from django.conf import settings

def build_ubuzima():
    try:
        initialize_reporttypes()
        import_cardcodes()
        build_alerts()
        return True
        
    except:
        pass
        return False


def loc_short_deletion():
	table='ubuzima_locationshorthand'
	cursor = connection.cursor()
	try:
		cursor.execute("drop table %s" % table)
		cursor.close()
	except Exception,e:
		raise e
		#pass
	return True
	
def hc_loc_short_creation():
	management.call_command('syncdb')
	hc=Location.objects.filter(type__in=[LocationType.objects.get(name='Health Centre'),LocationType.objects.get(name='Hospital')])
	hc=hc.exclude(id__in = [int(x.original.id) for x in LocationShorthand.objects.all()])
	anc,dst,prv,loc=[],None,None,None
	for hece in hc:
		anc,dst,prv,loc=[],None,None,None
		anc=Location.ancestors(hece)
		for an in anc:
			if an.type.name=='District': dst=an
			elif an.type.name=='Province': prv=an
		if prv is None or dst is None: return False
		loc=hece
		hece.district, hece.province, hece.nation = dst, prv, prv.parent
		hece.save()
		ls=LocationShorthand(original=loc, district=dst, province=prv)
		ls.save()
	return True

def build_old_fields():
    table='ubuzima_report_fields'
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM `%s` , ubuzima_field WHERE %s.field_id = ubuzima_field.id AND ubuzima_field.report_id IS NULL" % (table, table))
        for r in cursor.fetchall():
            rpt=Report.objects.get(pk=r[1])
            f=Field.objects.get(pk=r[2])
            f.report, f.creation = rpt, rpt.created
            f.save()
        cursor.close()
    except Exception,e:
        raise e
		#pass
    return True

def build_edd():
	reps = Report.objects.filter(type__name__in = ["Pregnancy","Birth"])
	for r in reps:
		try:
			if r.type == ReportType.objects.get(name = "Pregnancy"):	r.edd_date, r.edd_anc2_date, r.edd_anc3_date, r.edd_anc4_date = Report.calculate_edd(r.date),  Report.calculate_edd(r.date) - datetime.timedelta(days = Report.DAYS_ANC2), Report.calculate_edd(r.date) - datetime.timedelta(days = Report.DAYS_ANC3), Report.calculate_edd(r.date) - datetime.timedelta(days = Report.DAYS_ANC4)
			elif r.type == ReportType.objects.get(name = "Birth"):	r.edd_pnc1_date, r.edd_pnc2_date, r.edd_pnc3_date = r.date + datetime.timedelta(days = Report.DAYS_PNC1), r.date + datetime.timedelta(days = Report.DAYS_PNC2), r.date + datetime.timedelta(days = Report.DAYS_PNC3)
			r.save()
		except Exception, e: continue
	return True
def solve_old_sql():
    cursor = connection.cursor()
    try:
        files = glob.glob('rapidsmsrw1000/apps/ubuzima/sql/*.sql')
        
        for f in files:
            try: cursor.execute("source %s/%s" % (settings.PROJECT_PATH, f))
            except: continue

        cursor.close()
    except Exception,e:
        raise e
    return True
def locate_reporter():
	reps = Reporter.objects.filter(district = None)
	for r in reps:
		try:
			r.district, r.province, r.nation = r.location.district, r.location.province, r.location.nation
			r.save()
		except:	continue
	return True

def locate_patient():
	reps = Patient.objects.filter(district = None)
	for r in reps:
		try:
			r.district, r.province, r.nation = r.location.district, r.location.province, r.location.nation
			r.save()
		except:	continue
	return True

def locate_user():
	reps = UserLocation.objects.all()#.filter(pk__gte = 35552)
	for r in reps:
		try:
			r.district, r.province, r.nation = r.location.district, r.location.province, r.location.nation
			r.save()
		except:	continue
	return True

def locate_report():
	reps = Report.objects.filter(district = None)#.filter(pk__gte = 35552)
	for r in reps:
		try:
			r.district, r.province, r.nation = r.location.district, r.location.province, r.location.nation
			r.save()
		except:	continue
	return True

def locate_refusal():
	reps = Refusal.objects.filter(district = None)#.filter(pk__gte = 35552)
	for r in reps:
		try:
			r.district, r.province, r.nation = r.reporter.location.district, r.reporter.location.province, r.reporter.location.nation
			r.save()
		except:	continue
	return True

def locate_departure():
	reps = Departure.objects.filter(district = None)#.filter(pk__gte = 35552)
	for r in reps:
		try:
			r.district, r.province, r.nation = r.reporter.location.district, r.reporter.location.province, r.reporter.location.nation
			r.save()
		except:	continue
	return True

def locate_reminder():
	reps = Reminder.objects.filter(district = None)#.filter(pk__gte = 35552)
	for r in reps:
		try:
			r.district, r.province, r.nation = r.reporter.location.district, r.reporter.location.province, r.reporter.location.nation
			r.save()
		except:	continue
	return True

def locate_alert():
	reps = TriggeredAlert.objects.filter(district = None)#.filter(pk__gte = 35552)
	for r in reps:
		try:
			r.district, r.province, r.nation = r.reporter.location.district, r.reporter.location.province, r.reporter.location.nation
			r.save()
		except:	continue
	return True

def locate_field():
	fs = Field.objects.filter(district = None).exclude( report = None)#.filter(pk__gte = 35552)
	for r in fs:
		try:
			r.district, r.province, r.nation, r.creation  = r.report.location.district, r.report.location.province, r.report.location.nation, r.report.created
			r.save()
		except:	continue
	return True

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
def import_provinces(filepath = "rapidsmsrw1000/apps/ubuzima/xls/locations.xls", sheetname = "PROVINCES", startrow = 1, maxrow = 416, coderow = 1, namerow = 2):
	locs = []
	cnt = import_location(filepath, sheetname, startrow, maxrow, coderow, namerow)
	for c in cnt:
		try:
			code , name = c['code'], c['name']
			p = Location.objects.get( name = "Rwanda", type__name = "Nation" )
			l = Location( code = code , name = name , parent = p , type = LocationType.objects.get( name = 'Province'))
			l.nation = p
			l.save()
		except Exception ,e:
			locs.append({'code' : c['code'], 'name': c['name'], 'error': e})			
			continue
	return locs
def import_districts(filepath = "rapidsmsrw1000/apps/ubuzima/xls/locations.xls", sheetname = "DISTRICTS", startrow = 1, maxrow = 416, coderow = 1, namerow = 2):
	locs = []
	cnt = import_location(filepath, sheetname, startrow, maxrow, coderow, namerow)
	for c in cnt:
		try:
			code , name = c['code'], c['name']
			p = Location.objects.get( code = code [0:len(code)-2] )
			l = Location( code = code , name = name , parent = p , type = LocationType.objects.get( name = 'District'))
			l.province, l.nation = p, p.parent
			l.save()
		except Exception ,e:
			locs.append({'code' : c['code'], 'name': c['name'], 'error': e})			
			continue
	return locs
def import_sectors(filepath = "rapidsmsrw1000/apps/ubuzima/xls/locations.xls", sheetname = "SECTORS", startrow = 1, maxrow = 416, coderow = 1, namerow = 2):
	locs = []
	cnt = import_location(filepath, sheetname, startrow, maxrow, coderow, namerow)
	for c in cnt:
		try:
			code , name = c['code'], c['name']
			p = Location.objects.get( code = code [0:len(code)-2] )
			l = Location( code = code , name = name , parent = p , type = LocationType.objects.get( name = 'Sector'))
			l.district, l.province, l.nation = p, p.parent, p.parent.parent
			l.save()
		except Exception ,e:
			locs.append({'code' : c['code'], 'name': c['name'], 'error': e})			
			continue
	return locs
def import_cells(filepath = "rapidsmsrw1000/apps/ubuzima/xls/locations.xls", sheetname = "CELLS", startrow = 1, maxrow = 2222, coderow = 1, namerow = 2):
	locs = []
	cnt = import_location(filepath, sheetname, startrow, maxrow, coderow, namerow)
	for c in cnt:
		try:
			code , name = c['code'], c['name']
			p = Location.objects.get( code = code [0:len(code)-2] )
			l = Location( code = code , name = name , parent = p , type = LocationType.objects.get( name = 'Cell'))
			l.sector, l.district, l.province, l.nation = p, p.parent, p.parent.parent, p.parent.parent.parent
			l.save()
		except Exception ,e:
			locs.append({'code' : c['code'], 'name': c['name'], 'error': e})			
			continue
	return locs

def import_villages(filepath = "rapidsmsrw1000/apps/ubuzima/xls/locations.xls", sheetname = "VILLAGES", startrow = 1, maxrow = 14584, coderow = 1, namerow = 2):
	bad_v = Location.objects.filter(type__name = "Village")
	for l in bad_v: 
		if len(l.code) < 10 : l.delete() #delete all vilages with wrong codes
	locs = []
	cnt = import_location(filepath, sheetname, startrow, maxrow, coderow, namerow)
	for c in cnt:
		try:
			code , name = c['code'], c['name']
			p = Location.objects.get( code = code [0:len(code)-2] )
			l = Location( code = code , name = name , parent = p , type = LocationType.objects.get( name = 'Village'))
			l.cell, l.sector, l.district, l.province, l.nation = p, p.parent, p.parent.parent, p.parent.parent.parent, p.parent.parent.parent.parent
			l.save()
		except Exception, e:
			locs.append({'code' : c['code'], 'name': c['name'], 'error': e})			
			continue
	return locs

def import_cardcodes(filepath = "rapidsmsrw1000/apps/ubuzima/xls/cardcodes.xls", sheetname = "Codes", keyrow = 1, descrow = 2, catrow = 3, valrow = 4, kwrow = 5):
    book    = open_workbook(filepath)
    sheet   = book.sheet_by_name(sheetname)
    
    for row_index in range(sheet.nrows):
        if row_index < 1: continue
        
        key     = sheet.cell(row_index,keyrow-1).value.strip().lower()
        desc    = sheet.cell(row_index,descrow-1).value.strip()
        cat     = sheet.cell(row_index,catrow-1).value.strip()
        kw     = sheet.cell(row_index,kwrow-1).value.strip()
        try:    category,created = FieldCategory.objects.get_or_create( name = cat)
        except: pass
        try:
            ft = FieldType.objects.get( key = key)
            ft.category = category
            
        except:
            try:    ft = FieldType( key = key, category = category)
            except: continue
        ft.kw = kw
        ft.description = desc
        ft.has_value = True if sheet.cell(row_index,valrow-1).value.strip() == 'YES' else False             
        ft.save()          
        
    return True

def build_alerts():
    fts = FieldType.objects.filter(category__name = 'Red Alert Codes')
    risks = FieldType.objects.filter(category__name__icontains = 'risk', key__in = ['ib',])
    triggers = set()
    for t in TriggeredText.objects.all():
        for tr in t.triggers.all(): triggers.add(tr)
    for ft in fts:
        if ft not in triggers:
            chw = "Ubutumwa bwanyu turabubonye, gerageza urebeko wafasha uwo mubyeyi, tubimenyesheje inzego zitanga ubufasha baragutabara."
            kw  = "Umujyanama %s atumenyeshejeko umubyeyi %s utuye mu mudugudu wa %s afite ikibazo : %s. Gerageza urebe uko mwamufasha. " 
            fr  = "Un agent de sante communautaire %s vient de rapporter que le patient %s qui habite au village %s a un probleme: %s. Veuillez l'aider s'il vous plait."
            en  = "The community health worker %s comes to report that the patient %s in the village %s has this problem: %s. Please follow up and help."
            text_chw = TriggeredText.objects.create( name = "%s-%s(to CHW)" % (ft.key.upper(), ft.description), destination = 'CHW', description = "A %s is ..." % ft.description,\
                                        message_kw = chw , message_fr = fr, message_en = en)
            text_sup = TriggeredText.objects.create( name = "%s-%s(to SUP)" % (ft.key.upper(), ft.description), destination = 'SUP', description = "A %s is ..." % ft.description,\
                                        message_kw = kw , message_fr = fr, message_en = en)
            text_amb = TriggeredText.objects.create( name = "%s-%s(to AMB)" % (ft.key.upper(), ft.description), destination = 'AMB', description = "A %s is ..." % ft.description,\
                                        message_kw = kw , message_fr = fr, message_en = en)
            text_dis = TriggeredText.objects.create( name = "%s-%s(to DIS)" % (ft.key.upper(), ft.description), destination = 'DIS', description = "A %s is ..." % ft.description,\
                                        message_kw = kw , message_fr = fr, message_en = en)

            text_chw.triggers.add(ft);text_chw.save()
            text_sup.triggers.add(ft);text_sup.save()
            text_amb.triggers.add(ft);text_amb.save()
            text_dis.triggers.add(ft);text_dis.save()

#    for ft in risks:
#        chw = "Ubutumwa bwanyu turabubonye, gerageza urebeko wafasha uwo mubyeyi, tubimenyesheje inzego zitanga ubufasha nibiba ngombwa baragutabara."
#        kw  = "Umujyanama %s atumenyeshejeko umubyeyi %s utuye mu mudugudu wa %s afite ikibazo : %s. Gerageza urebe uko mwamufasha. " 
#        fr  = "Un agent de sante communautaire %s vient de rapporter que le patient %s qui habite au village %s a un probleme: %s. Veuillez l'aider s'il vous plait."
#        en  = "The community health worker %s comes to report that the patient %s in the village %s has this problem: %s. Please follow up and help."
#        text_chw = TriggeredText.objects.create( name = "%s-%s(to CHW)" % (ft.key.upper(), ft.description), destination = 'CHW',\
#                                                 description = "A %s is ..." % ft.description, message_kw = chw , message_fr = fr, message_en = en)
#        text_sup = TriggeredText.objects.create( name = "%s-%s(to SUP)" % (ft.key.upper(), ft.description), destination = 'SUP', \
#                                                 description = "A %s is ..." % ft.description, message_kw = kw , message_fr = fr, message_en = en)
#        text_amb = TriggeredText.objects.create( name = "%s-%s(to AMB)" % (ft.key.upper(), ft.description), destination = 'AMB', active = False,\
#                                                 description = "A %s is ..." % ft.description, message_kw = kw , message_fr = fr, message_en = en)
#        text_dis = TriggeredText.objects.create( name = "%s-%s(to DIS)" % (ft.key.upper(), ft.description), destination = 'DIS', active = False,\
#                                                 description = "A %s is ..." % ft.description, message_kw = kw , message_fr = fr, message_en = en)
#
#        text_chw.triggers.add(ft);text_chw.save()
#        text_sup.triggers.add(ft);text_sup.save()
#        text_amb.triggers.add(ft);text_amb.save()
#        text_dis.triggers.add(ft);text_dis.save()            
            
    return True

def initialize_reporttypes():
    t = ['ANC', 'Birth', 'Community Based Nutrition', 'Community Case Management', 'Child Health', 'Case Management Response', 'Death', 'Newborn Care', \
            'PNC', 'Pregnancy', 'Red Alert Result', 'Red Alert', 'Risk Result', 'Risk', 'Refusal', 'Departure' ]
    try:
        for r in t:
            ReportType.objects.get_or_create(name = r)
    except: pass
    return True
        

def build_reminders():
    rems = Reminder.objects.all()
    for reminder in rems:
        reporter = reminder.reporter
        reminder.village = reporter.village
        reminder.cell = reporter.cell
        reminder.sector = reporter.sector
        reminder.district = reporter.district
        reminder.province = reporter.province
        reminder.nation = reporter.nation
        reminder.save()
    return True


def update_locations():
	locs = []
	for l in Location.objects.all():
		try: 
			p = l.parent
			if l.type == LocationType.objects.get( name = 'Village') and l.cell is None:
				l.cell, l.sector, l.district, l.province, l.nation = p, p.parent, p.parent.parent, p.parent.parent.parent, p.parent.parent.parent.parent
			if l.type == LocationType.objects.get( name = 'Cell') and l.sector is None:
				l.cell,l.sector, l.district, l.province, l.nation =l, p, p.parent, p.parent.parent, p.parent.parent.parent
			
			if l.type == LocationType.objects.get( name = 'Sector') and l.district is None:
				l.sector,l.district, l.province, l.nation =l, p, p.parent, p.parent.parent
			if l.type == LocationType.objects.get( name = 'District'):
				l.district,l.province, l.nation =l, p, p.parent
			if l.type == LocationType.objects.get( name = 'Province') and l.nation is None:
				l.province,l.nation = l,p
			l.save()
		except Exception, e:
			locs.append({'code' : l.code, 'name': l.name, 'error': e})			
			continue

	return locs


def export_patients():
    import xlwt
    wbk = xlwt.Workbook()
    pts = Patient.objects.all()
    nsheets = pts.count()/65536
    if pts.count()%65536 != 0:
        nsheets = nsheets+1
    for n in range(nsheets):
        ans = pts[n*65536: (n+1)*65536]
        sheet = wbk.add_sheet("Patient List %d " % n) 
        sheet.write(0,0,"National ID")
        sheet.write(0,1,"Village")
        sheet.write(0,2,"Cell")
        sheet.write(0,3,"Sector")
        sheet.write(0,4,"District")
        sheet.write(0,5,"Province")
        row = 1
        for pt in ans:
            try: sheet.write(row,0,pt.national_id)
            except: continue
            try: sheet.write(row,1,pt.village.name)
            except: pass
            try: sheet.write(row,2,pt.cell.name)
            except: pass
            try: sheet.write(row,3,pt.sector.name)
            except: pass
            try: sheet.write(row,4,pt.district.name)
            except: pass
            try: sheet.write(row,5,pt.province.name)
            except: pass
            row = row+1
    today = datetime.date.today()
    wbk.save('patients_%s_%s_%s.xls' % (today.day, today.month, today.year))
    return True


###Retrieve all reporters in traning db module		
#def reporters_in_training():
#	reps_training_nid = []	
#	cursor = connection.cursor()
#	cursor.execute("SELECT * FROM ubuzima_training_db.reporters_reporter , ubuzima_training_db.reporters_persistantconnection WHERE ubuzima_training_db.reporters_reporter.id = ubuzima_training_db.reporters_persistantconnection.id ")
#
#	for r in cursor.fetchall(): 
#		reps_training_nid.append({'nid' : r[1], 'identity' : r[11], 'location' : r[4], 'village' : r[6] , 'lang' : r[7]})
#	
#	cursor.close()	
#	return reps_training_nid
####retrieve all reporters in production db module
#def reporters_in_production():
#	reps_production = Reporter.objects.all()
#	reps_production_nid = []
#	for r in reps_production:
#		try:	reps_production_nid.append( {'nid' : r.alias, 'identity' : r.connection().identity, 'location' : r.location, 'village' : r.village , 'lang' : #r.language} )
#		except : continue
#
#	return reps_production_nid
### Retrieve reporters in production withour telephone numbers
#def reporters_in_production_without_identinty():
	
#	return Reporter.objects.filter(connections = None)

######retrieve reporters in production without health centre assigned.
#def reporters_in_production_without_location():
#	
#	return Reporter.objects.filter(location = None)

### reporters in training db module not in production
#def reporters_in_training_not_in_production():
#	t = reporters_in_training()
#	p = [ k['identity'] for k in reporters_in_production()]
#	dif = []
#	for s in t:
#		if s['identity'] not in p:	dif.append(s)
#	return dif 
### exports to csv or Excell, reporters in training db module not in production	, for further analysis
#def export_reporters_in_training_not_in_production():
	
#	with open('/home/zigama/Desktop/reporters_in_training_not_in_production.csv', 'wb') as fout:
#		writer = csv.writer(fout)
#		writer.writerow([ 'ReporterNID','Location','Telephone','Village','District','Province','Language']) # heading row
#		for r in reporters_in_training_not_in_production():
#			try:
#				if Location.objects.filter(pk = r['location']).exists():
#					l = Location.objects.filter(pk = r['location'])[0]
#					writer.writerow([ r['nid'], l.name, r['identity'], r['village'], l.district.name, l.province.name, r['lang']])
#				else:	writer.writerow([ r['nid'], "Unknown", r['identity'], r['village'], "Unknown", "Unknown", r['lang']])
#			except:	continue
#	return True

#def export_reporters_in_production_without_location():
	
#	with open('/home/zigama/Desktop/reporters_in_production_without_location.csv', 'wb') as fout:
#		writer = csv.writer(fout)
#		writer.writerow([ 'ReporterNID','Location','Telephone','Village','District','Province','Language']) # heading row
#		for r in reporters_in_production_without_location():
#			try:
#				if Location.objects.filter(pk = r['location']).exists():
#					l = Location.objects.filter(pk = r['location'])[0]
#					writer.writerow([ r['nid'], l.name, r['identity'], r['village'], l.district.name, l.province.name, r['lang']])
#				else:	writer.writerow([ r['nid'], "Unknown", r['identity'], r['village'], "Unknown", "Unknown", r['lang']])
#			except:	continue
#	return True

#def export_reporters_in_production_without_identinty():
	
#	with open('/home/zigama/Desktop/reporters_in_production_without_identinty.csv', 'wb') as fout:
#		writer = csv.writer(fout)
#		writer.writerow([ 'ReporterNID','Location','Telephone','Village','District','Province','Language']) # heading row
#		for r in reporters_in_production_without_identinty():
#			try:
#				if Location.objects.filter(pk = r['location']).exists():
#					l = Location.objects.filter(pk = r['location'])[0]
#					writer.writerow([ r['nid'], l.name, r['identity'], r['village'], l.district.name, l.province.name, r['lang']])
#				else:	writer.writerow([ r['nid'], "Unknown", r['identity'], r['village'], "Unknown", "Unknown", r['lang']])
#			except:	continue
#	return True



#### START OF SENDING APPROPRIATE SMS, TO COMPLETE REGISTRATION

####Redirect reporters to 1110 from 3014
#def leave_3014(reporters = reporters_in_training_not_in_production()):
#	for r in reporters:
#		x = Smser().send_message_via_kannel(r['identity'], "Mwaramutse! Minisiteri y'ubuzima yabasabagako mwajya mwohereza ubutumwa ku buzima bw'umwana n'umubyeyi kuri numero ya telephoni 1110. Murakoze.")	

#### END OF SENDING APPROPRIATE SMS, TO COMPLETE REGISTRATION


