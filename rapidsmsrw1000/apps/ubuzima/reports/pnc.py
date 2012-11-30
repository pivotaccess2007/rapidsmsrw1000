####SAMPLE MESSAGE #####
##res_EN = "The correct format message is: PNC MOTHER_ID PNC_ROUND DOB SYMPTOMS INTERVENTION CHILD_STATUS"
##res_FR = "Andika: NBC INDANGAMUNTU INSHURO ITARIKI_YAVUTSE IBIBAZO UBUTABAZI UKO_UMWANA_AMEZE"
##msg = "PNC 1198156435491265 PNC3 13.02.2011 HE NP PR MW CW"
###m = re.search("pnc\s+(\d+)\s+(pnc1|pnc2|pnc3)\s([0-9.]+)\s?(.*)\s(pt|pr|tr|aa|al|at|na)\s(mw|ms|cw|cs)\s?(.*)", msg, re.IGNORECASE)   
###groups = ('1198156435491265', 'PNC3', '13.02.2011', 'HE NP', 'PR', 'MW', 'CW')
#        nid = m.group(1)
#        tour = m.group(2)
#        chidob = m.group(3)
#        ibibazo = m.group(4)
#        intervention = m.group(5)
#        mstatus = m.group(6)
#        cstatus = m.group(7)

    #PNC keyword
    @keyword("\s*pnc(.*)")
    def pnc(self, message, notice):
        """PNC report.  """
        
        if not getattr(message, 'reporter', None):
            message.respond(_("You need to be registered first, use the REG keyword"))
            return True
            
        m = re.search("pnc\s+(\d+)\s+(pnc1|pnc2|pnc3)\s([0-9.]+)\s?(.*)\s(pt|pr|tr|aa|al|at|na)\s(mw|ms|cw|cs)\s?(.*)", message.text, re.IGNORECASE)
        if not m:
            message.respond(_("The correct format message is: PNC MOTHER_ID PNC_ROUND DOB SYMPTOMS INTERVENTION CHILD_STATUS"))
            return True

        nid = m.group(1)
        tour = m.group(2)
        chidob = m.group(3)
        ibibazo = m.group(4)
        intervention = m.group(5)
        mstatus = m.group(6)
        cstatus = m.group(7)

        # get or create the patient
        patient = self.get_or_create_patient(message.reporter, nid)
        
        report = self.create_report('Postnatal Care', patient, message.reporter)
        
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
        report.save()
                
        # then associate all our fields with it
        
        fields.append(self.read_key(tour))
        for st in self.read_fields(cstatus, False, False)[0]:	fields.append(st)
        fields.append(self.read_key(mstatus))
        fields.append(self.read_key(intervention))


        for field in fields:
            field.save()
            report.fields.add(field)            
        
        # either send back the advice text or our default msg
        try:	response = self.run_triggers(message, report)
        except:	response = None
        if response:
            message.respond(response)
        else:
            message.respond(_("Thank you! PNC report submitted successfully."))
            
        # cc the supervisor if there is one
        try:	self.cc_supervisor(message, report)
   	except:	pass  
    	        
        return True
    
        #PNC keyword

