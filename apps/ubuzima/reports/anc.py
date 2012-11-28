####SAMPLE MESSAGE #####
##res_EN = "The correct format message is: PRE MOTHER_ID LAST_MENSES NEXT_VISIT PREVIOUS_RISK CURRENT_RISK LOCATION_CODE MOTHER_WEIGHT MOTHER_HEIGHT SANITATION TELEPHONE"
##res_FR = "Andika: PRE INDANGAMUNTU ITARIKI_YIMIHANGO IYOGUSUBIRAYO INSHURO_YASAMYE IZAVUTSE IBIBAZO_KERA IBISHYA AHO_YAPIMIWE IBIRO UBUREBURE UMUSARANI KANDAGIRA TELEFONI"
##msg = "PRE 1198156435491265 13.02.2011 15.05.2011 02 01 MU NP HP WT72.3 HT165 TO NH 0788660270"
###m = re.search("pre\s+(\d+)\s+([0-9.]+)\s([0-9.]+)\s([0-9]+)\s([0-9]+)\s?(.*)\s(hp|cl)\s(wt\d+\.?\d)\s(ht\d+\.?\d)\s(to|nt)\s(hw|nh)\s?(.*)", msg, re.IGNORECASE)   
###groups = ('1198156435491265', '13.02.2011', '15.05.2011', '02', '01', 'MU NP', 'HP', 'WT72.3', 'HT165', 'TO', 'NH', '0788660270')
#        nid = m.group(1)
#        lmp = m.group(2)
#        next_visit = m.group(3)
#        gravity = m.group(4)
#        parity = m.group(5)
#        ibibazo = m.group(6)
#        location = m.group(7)
#        weight = m.group(8)
#        height = m.group(9)
#        toilet = m.group(10)
#        handwash = m.group(11)
#        telephone = m.group(12)

    @keyword("\s*anc(.*)")
    def anc(self, message, notice):
    	"""New Anc report. This is for regestering a new anc visit ."""
    	if not getattr(message, 'reporter', None):
            message.respond(_("You need to be registered first, use the REG keyword"))
            return True
    	
	m = re.search("anc\s+(\d+)\s?(.*)", message.text, re.IGNORECASE)
        if not m:
            message.respond(_("The correct format message is: ANC MOTHER_ID ..."))
            return True
    	received_patient_id = m.group(1)
	optional_part=m.group(2)
	anc_report=re.match("([0-9.]+)\s+(.*(\s*(anc2|anc3|anc4)\s*).*(\d+\.?\d*)(k|kg|kilo|kilogram).*)",optional_part,re.IGNORECASE)
    	anc_dep=re.match("(dp)\s?(.*)",optional_part,re.IGNORECASE)
    	last_visit=date.today()
	if anc_report:
		try:
		    last_visit = self.parse_dob(anc_report.group(1))
		except Exception, e:
		    # date was invalid, respond
		    message.respond("%s" % e)
		    return True
		
    			
    	if anc_dep:
		pass		
	if not anc_report and not anc_dep:
		message.respond(_("The correct format message is: ANC MOTHER_ID LAST_VISIT ANC_ROUND ACTION_CODE MOTHER_WEIGHT"))
    		return True
    	
    	if anc_report or anc_dep:
	    	# get or create the patient
		patient = self.get_or_create_patient(message.reporter, received_patient_id)

		# create our report
		report = self.create_report('ANC', patient, message.reporter)
    	#date of last visit
    	if anc_report:
    		report.set_date_string(last_visit)
	    	# read our fields
	try:
	    (fields, dob) = self.read_fields(optional_part,False, True)
	except Exception, e:
	    # there were invalid fields, respond and exit
	    message.respond("%s" % e)
	    return True

	# save the report
	if not report.has_dups():
        	report.save()
        else:
    		message.respond(_("This report has been recorded, and we cannot duplicate it again. Thank you!"))
    		return True
	
	# then associate all the action codes with it
	for field in fields:
	    field.save()
	    report.fields.add(field)            
	
	# either send back the advice text or our default msg
	if not Report.objects.filter(patient=patient,type__name='Pregnancy',created__gte=(date.today()-timedelta(270))):
		message.respond("Thank you! ANC report submitted. Please send also the pregnancy report of this patient (%s)."%str(patient))
		return True
	response = self.run_triggers(message, report)
	if response:
	    message.respond(response)
	else:
	    message.respond(_("Thank you! ANC report submitted successfully."))
	    
	# cc the supervisor if there is one
	self.cc_supervisor(message, report)
        return True 

    #   TODO:
    #   Muck with the translations.
