####SAMPLE MESSAGE #####
##res_EN = "The correct format message is: DTH MOTHER_ID CHILD_NUMBER DATE_OF_BIRTH DEATH_CODE"
##res_FR = "Andika: DTH INDANGAMUNTU NUMERO_Y_UMWANA ITARIKI_Y_AMAVUKO CODI_Y_URUPFU"
##msg = "DTH 1198156435491265 01 15.05.2011 ND"
###m = re.search("dth\s+(\d+)\s+([0-9]+)\s([0-9.]+)\s(nd|cd|md)\s?(.*)", msg, re.IGNORECASE)   
###groups = ('1198156435491265', '01', '15.05.2011', 'ND', '')
#        nid = m.group(1)
#        number = m.group(2)
#        chidob = m.group(3)
#        ibibazo = m.group(4)

    @keyword("\s*dth(.*)")
    def death(self, message, notice):
        """DEATH report, represents a possible death, can trigger alerts."""
        
        if not getattr(message, 'reporter', None):
            message.respond(_("You need to be registered first, use the REG keyword"))
            return True
            
        m = re.search("dth\s+(\d+)\s+(?.*|[0-9]+)\s(?.*|[0-9.]+)\s(nd|cd|md)\s?(.*)", message.text, re.IGNORECASE)
        if not m:
            message.respond(_("The correct format message is: DTH MOTHER_ID CHILD_NUMBER DATE_OF_BIRTH DEATH_CODE"))
            return True

        nid = m.group(1)
        number = m.group(2)
        chidob = m.group(3)
        ibibazo = m.group(4)

        # get or create the patient
        patient = self.get_or_create_patient(message.reporter, nid)

        report = self.create_report('Death', patient, message.reporter)
        
        # Line below may be needed in case Risk reports are sent without previous Pregnancy reports
        #location = message.reporter.location
        
        # read our fields
        try:
            (fields, dob) = self.read_fields(ibibazo, False, False)
    	    dob = self.parse_dob(chidob)
        except Exception, e:
            # there were invalid fields, respond and exit
            message.respond("%s" % e)
            return True

        # set the dob for the child if we got one
        if dob:
            report.set_date_string(dob)

        # save the report
        if not report.has_dups():
        	report.save()
        else:
    		message.respond(_("This report has been recorded, and we cannot duplicate it again. Thank you!"))
    		return True


        
	# then associate all our fields with it
        
        fields.append(self.read_number(number))
        for field in fields:
            field.save()
            report.fields.add(field)
            
        # either send back our advice text or our default response
        try:	response = self.run_triggers(message, report)
        except:	response = None
        if response:
            message.respond(response)
        else:
            message.respond(_("Thank you! Death report submitted successfully."))
            
        # cc the supervisor if there is one
        try:	self.cc_supervisor(message, report)
   	except:	pass  
        

        return True
