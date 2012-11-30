####SAMPLE MESSAGE #####
##res_EN = "The correct format message is: CMR MOTHER_ID CHILD_NUM DOB SYMPTOMS INTERVENTION MOTHER_STATUS CHILD_STATUS"
##res_FR = "Andika: CMR INDANGAMUNTU NUMERO_Y_UMWANA ITARIKI_YAVUTSE IBIBAZO UBUTABAZI UKO_UMUBYEYI_AMEZE UKO_UMWANA_AMEZE"
##msg = "CMR 1198156435491265 01 13.02.2011 MA PR CW"
###m = re.search("cmr\s+(\d+)\s+([0-9]+)\s([0-9.]+)\s?(.*)\s(pt|pr|tr|aa|al|at|na)\s(mw|ms|cw|cs)\s?(.*)", msg, re.IGNORECASE)  
###groups = ('1198156435491265', '01', '13.02.2011', 'MA', 'PR', 'CW', '')
#        nid = m.group(1)
#        number = m.group(2)
#        chidob = m.group(3)
#        ibibazo = m.group(4)
#        intervention = m.group(5)
#        mstatus = m.group(6)
#        cstatus = m.group(7)

    #CMR keyword
    @keyword("\s*cmr(.*)")
    def cmr(self, message, notice):
        """CMR report.  """
        
        if not getattr(message, 'reporter', None):
            message.respond(_("You need to be registered first, use the REG keyword"))
            return True
            
        m = re.search("cmr\s+(\d+)\s+([0-9]+)\s([0-9.]+)\s?(.*)\s(pt|pr|tr|aa|al|at|na)\s(mw|ms|cw|cs)\s?(.*)", message.text, re.IGNORECASE)
        if not m:
            message.respond(_("The correct format message is: CMR MOTHER_ID CHILD_NUM DOB SYMPTOMS INTERVENTION MOTHER_STATUS CHILD_STATUS"))
            return True

        nid = m.group(1)
        number = m.group(2)
        chidob = m.group(3)
        ibibazo = m.group(4)
        intervention = m.group(5)
        mstatus = m.group(6)
        cstatus = m.group(7)

        # get or create the patient
        patient = self.get_or_create_patient(message.reporter, nid)
        
        report = self.create_report('Case Management Response', patient, message.reporter)
        
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
            
        # set the child number
        child_num_type = FieldType.objects.get(key='child_number')
        fields.append(Field(type=child_num_type, value=Decimal(str(number))))

        # save the report
        report.save()
                
        # then associate all our fields with it
        fields.append(self.read_key(intervention))
        fields.append(self.read_key(mstatus))
        for st in self.read_fields(cstatus, False, False)[0]:	fields.append(st)

        for field in fields:
            field.save()
            report.fields.add(field)            
        
        # either send back the advice text or our default msg
        try:	response = self.run_triggers(message, report)
        except:	response = None
        if response:
            message.respond(response)
        else:
            message.respond(_("Thank you! CMR report submitted successfully."))
            
        # cc the supervisor if there is one
        try:	self.cc_supervisor(message, report)
   	except:	pass  
    	        
        return True
    
        #CMR keyword

