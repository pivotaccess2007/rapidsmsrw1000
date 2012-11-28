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

@keyword("\s*pre(.*)")
def pregnancy(self, message, notice):
        """Incoming pregnancy reports.  This registers a new mother as having an upcoming child"""

        self.debug("PRE message: %s" % message.text)

        if not getattr(message, 'reporter', None):
            message.respond(_("You need to be registered first, use the REG keyword"))
            return True

        m = re.search("pre\s+(\d+)\s+([0-9.]+)\s([0-9.]+)\s([0-9]+)\s([0-9]+)\s?(.*)\s(hp|cl)\s(wt\d+\.?\d)\s(ht\d+\.?\d)\s(to|nt)\s(hw|nh)\s?(.*)",\
			 message.text, re.IGNORECASE)
        if not m:
            message.respond(_("The correct format message is: PRE MOTHER_ID LAST_MENSES NEXT_VISIT PREVIOUS_RISK CURRENT_RISK LOCATION_CODE MOTHER_WEIGHT MOTHER_HEIGHT SANITATION TELEPHONE"))
            return True
        
        nid = m.group(1)
        lmp = m.group(2)
        next_visit = m.group(3)
        gravity = m.group(4)
        parity = m.group(5)
        ibibazo = m.group(6)
        location = m.group(7)
        weight = m.group(8)
        height = m.group(9)
        toilet = m.group(10)
        handwash = m.group(11)
        telephone = m.group(12)
        
        try:
            last_menses = self.parse_dob(lmp)
        except Exception, e:
            # date was invalid, respond
            message.respond("%s" % e)
            return True
            
    	
        # get or create the patient
        patient = self.get_or_create_patient(message.reporter, nid)
        
        # create our report
        report = self.create_report('Pregnancy', patient, message.reporter)

        report.set_date_string(last_menses)
        
        # read our fields
        try:
            (fields, dob) = self.read_fields(ibibazo, False, False)
        except Exception, e:
            # there were invalid fields, respond and exit
            message.respond("%s" % e)
            return True
        
        # save the report
    	if not report.has_dups():
		report.save()
		    		
		try:

    			pregnancy = Pregnancy(report = report, plmp = datetime.strptime(self.parse_dob(lmp), "%d.%m.%Y").date(), \
						pnext_visit = datetime.strptime(self.parse_date(next_visit), "%d.%m.%Y").date(), mtelephone = "+25%s"%telephone)
    			pregnancy.save()
		except Exception, e:
			report.delete()	
			message.respond(_("Unknown Error, please check message format and try again."))	
        else:
    		message.respond(_("This report has been recorded, and we cannot duplicate it again. Thank you!"))
    		return True
        # then associate all our fields with it
        fields.append(self.read_weight(weight, weight_is_mothers=True))
        fields.append(self.read_height(height, height_is_mothers=True))
        fields.append(self.read_key(toilet))
        fields.append(self.read_key(handwash))
        fields.append(self.read_key(location))
        for field in fields:
            if field:
    	    	field.save()
            	report.fields.add(field)            

        # either return an advice text, or our default text for this message type
        try:	response = self.run_triggers(message, report)
        except:	response = None
        if response:
            message.respond(response)
        else:
            message.respond(_("Thank you! Pregnancy report submitted successfully."))
            
        # cc the supervisor if there is one
        try:	self.cc_supervisor(message, report)
   	except:	pass  
  
        
        return True



