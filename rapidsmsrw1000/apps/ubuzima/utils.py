import xlwt


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

	

