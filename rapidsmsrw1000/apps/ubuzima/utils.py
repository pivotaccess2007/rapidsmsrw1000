import xlwt
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseServerError, HttpResponseRedirect,Http404

#wbk = xlwt.Workbook()
#sheet.write(0,0,"ReportID")
#sheet.write(0,1,"Date")
#sheet.write(0,2,"Location")
#sheet.write(0,3,"District")
#sheet.write(0,4,"Type")
#sheet.write(0,5,"Reporter")
#sheet.write(0,6,"Patient")
#sheet.write(0,7,"Message")


#row = 1
#for r in reports:
#  sheet.write(row,0,r.pk)
#  sheet.write(row,1,"%d.%d.%d" % (r.created.day,r.created.month,r.created.year))
#  sheet.write(row,2,r.location.name)
#  sheet.write(row,3,r.location.parent.parent.name)
#  sheet.write(row,4,r.type.name)
#  sheet.write(row,5,r.reporter.alias)
#  sheet.write(row,6,r.patient.national_id)
#  sheet.write(row,7,r.summary())
#  row = row+1

#wbk.save('xlwt.xls')####This allows the workbook to be saved on the disk

def create_workbook():
	
	return xlwt.Workbook()

def create_worksheet( workbook, name = "Export"):

	return workbook.add_sheet(name)

def create_heads(sheet, heads): 
	"""sheet = xlwt sheet object ... eg sheet = xlwt.Workbook().add_sheet("Reports"), 
           heads =  a list of headers ... eg : heads = ['ReportID','Date','Location','District','Type','Reporter','Patient','Message'] """

	hl = len(heads)
	row, col = 0, 0 
	for h in heads:
		if col == hl:
			break
		else:
			sheet.write(row, col, heads[col])
			col = col + 1

	return sheet



def create_content(sheet, row, content_list):
	"""sheet = xlwt sheet object ... eg sheet = xlwt.Workbook().add_sheet("Reports"), 
           heads =  a list of headers ... eg : content_list = [r.id, "%d.%d.%d" % (r.created.day,r.created.month,r.created.year),r.location.name,r.location.parent.parent.name,r.type.name,r.reporter.alias,r.patient.national_id, r.summary()] """

		
	cl = len(content_list)
	col = 0 
	for item in content_list:
		if col == cl:
			break
		else:
			sheet.write(row, col, content_list[col])
			col = col + 1
	

	return sheet

def heading_report(report):
	heads = ['ReportID','Date','Facility', 'District', 'Province','Type','Reporter','Patient', 'LMP','EDD', 'DOB', 'VisitDate',' ANCVisit','NBCVisit','PNCVisit','MotherWeight','MotherHeight','ChildWeight','ChildHeight','MUAC', 'ChilNumber','Gender', 'Gravidity','Parity', 'VaccinationReceived' , 'VaccinationCompletion','Breastfeeding', 'Intevention', 'Status','Toilet','Handwash' , 'Located','Symptoms']

	dob = lmp = edd = visit = anc = nbc = pnc = mother_w = child_w = mother_h = child_h = muac = chino = gender = gr = pr = vr = vc = bf = interv = st = toi = hw = loc = sym = ""
	
	try:
		mother_wf = report.fields.filter(type__key = 'mother_weight')
		for s in mother_wf:
			mother_w = mother_w.join("%d" % s.value)
	except:	pass
	try:
		mother_hf = report.fields.filter(type__key = 'mother_height')
		for s in mother_hf:
			mother_h = mother_h.join("%d" % s.value)
	except:	pass
	try:
		child_wf = report.fields.filter(type__key = 'child_weight')
		for s in child_wf:
			child_w = child_w.join("%d" % s.value)
	except:	pass
	try:
		child_hf = report.fields.filter(type__key = 'child_height')
		for s in child_hf:
			child_h = child_h.join("%d" % s.value)
	except:	pass
	try:
		ancf = report.fields.filter(type__key__in = ['anc2','anc3','anc4'])
		for s in ancf:
			anc = anc.join("%s" % s.type.description)
	except:	pass
	try:
		pncf = report.fields.filter(type__key__in = ['pnc1','pnc2','pnc3'])
		for s in pncf:
			pnc = pnc.join("%s" % s.type.description)
	except:	pass
	try:
		nbcf = report.fields.filter(type__key__in = ['nbc1','nbc2','nbc3','nbc4','nbc5'])
		for s in nbcf:
			nbc = nbc.join("%s" % s.type.description)
	except:	pass
	try:
		muacf = report.fields.filter(type__key = 'muac')
		for s in muacf:
			muac = muac.join("%d" % s.value)
	except:	pass
	try:
		chinof = report.fields.filter(type__key = 'child_number')
		for s in chinof:
			chino = chino.join("%d" % s.value)
	except:	pass
	try:
		genderf = report.fields.filter(type__key__in = ['gi','bo'])
		for s in genderf:
			gender = gender.join("%s" % s.type.description)
	except:	pass
	try:
		grf = report.fields.filter(type__key = 'gravity')
		for s in grf:
			gr = gr.join("%d" % s.value)
	except:	pass

	try:
		prf = report.fields.filter(type__key = 'parity')
		for s in prf:
			pr = pr.join("%d" % s.value)
	except:	pass
	try:
		vrf = report.fields.filter(type__key__in = ['v1','v2','v3','v4','v5','v6'])
		for s in vrf:
			vr = vr.join("%s" % s.type.description)
	except:	pass
	try:
		vcf = report.fields.filter(type__key__in = ['vc', 'vi', 'nv'])
		for s in vcf:
			vc = vc.join("%s" % s.type.description)
	except:	pass
	try:
		bff = report.fields.filter(type__key__in = ['ebf','cbf','nb'])
		for s in bff:
			bf = bf.join("%s" % s.type.description)
	except:	pass
	try:
		 
		intervf = report.fields.filter(type__category__name = 'Intervention Codes')
		for s in intervf:
			interv = interv.join("%s" % s.type.description)
	except:	pass
	try:
		locf = report.fields.filter(type__category__name = 'Location Codes')
		for s in locf:
			loc = loc.join("%s" % s.type.description)
	except:	pass
	try:
		stf = report.fields.filter(type__category__name = 'Results Codes')
		for s in stf:
			st = st+s.type.description+", "
	except:	pass
	try:
		hwf = report.fields.filter(type__key__in = ['hw','nh'])
		for s in hwf:
			hw = hw.join("%s" % s.type.description)
	except:	pass
	try:
		toif = report.fields.filter(type__key__in = ['to', 'nt'])
		for s in toif:
			toi = toi.join("%s" % s.type.description)
	except:	pass

	try:
		symf = report.fields.filter(type__category__name__in = ['Risk Codes' , 'Red Alert Codes', 'PRE Codes']).exclude(type__key__in = \
						['nh', 'nt', 'to', 'hw', 'gravity', 'parity'])
		for s in symf:
			sym = sym+s.type.description+", "
	except:	pass
	#print 'id:%s'%report.id, 'date:%s'%read_date(report.created), 'fac:%s'%report.location.name, 'dist:%s'%report.district.name, 'prv:%s'%report.province.name, 'rty:%s'%report.type.name , 'rnid:%s'%report.reporter.telephone_moh, 'pnid:%s'%report.patient.national_id , 'lmp:%s'%lmp, 'dob:%s'%dob, 'visit:%s'%visit, 'anc:%s'%anc, 'nbc:%s'%nbc, 'pnc:%s'%pnc, 'm_w:%s'%mother_w, 'm_h:%s'%mother_h, 'c_w:%s'%child_w, 'c_w:%s'%child_h, 'muac:%s'%muac, 'chino:%s'%chino, 'gender:%s'%gender, 'gr:%s'%gr, 'pr:%s'%pr, 'vr:%s'%vr, 'vc:%s'%vc, 'bf:%s'%bf, 'interv:%s'%interv, 'st:%s'%st, 'toi:%s'%toi, 'hw:%s'%hw, 'loc:%s'%loc, 'sym:%s'%sym
	

	if report.type.name == 'Birth': dob = read_date(report.date)
	elif report.type.name == 'Pregnancy': lmp, edd =  read_date(report.date), read_date(report.edd_date)
	elif report.type.name == 'ANC': visit = read_date(report.date)
	else:	dob = read_date(report.date)  

	content = [report.id, read_date(report.created), report.location.name, report.district.name, report.province.name, report.type.name , report.reporter.national_id, report.patient.national_id , lmp, edd, dob, visit, anc,nbc, pnc, mother_w, mother_h, child_w, child_h, muac, chino, gender, gr, pr, vr, vc, bf, interv, st, toi, hw, loc, sym ]

	return {'heads' : heads, 'content' : content}

def reports_to_excel(reports):
	maquis = heading_report(reports[1])
	workbook = create_workbook()
	sheet = create_worksheet(workbook, "reports")
	sheet = create_heads(sheet, maquis['heads'])
	row   = 1
	for report in reports:
		sheet  = create_content(sheet, row, heading_report(report)['content'])
        
		row = row + 1
    
	response = HttpResponse(mimetype = "application/ms-excel")
	response['Content-Disposition'] = 'attachment; filename = reports.xls'
	workbook.save(response)
	return response

def read_date(date):
	try: return "%d/%d/%d" %  (date.day, date.month, date.year)
	except:	return ""
		

