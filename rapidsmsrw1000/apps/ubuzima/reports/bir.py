####SAMPLE MESSAGE #####
##res_EN = "The correct format message is: BIR MOTHER_ID TWINS CHILD_NUM DOB SEX ACTION_CODE LOCATION_CODE BREASTFEEDING CHILD_WEIGHT"
##res_FR = "Andika: BIR INDANGAMUNTU IMPANGA NUMERO ITARIKI_AVUTSE IGITSINA IBIBAZO AHO_AVUKIYE KONKA IBIRO"
##msg = "BIR 1198156435491265 TW 01 13.02.2011 GI PM NP HP BF1 WT72.3"
###m = re.search("bir\s+(\d+)\s?(.*|tw|tr)\s([0-9]+)\s([0-9.]+)\s(bo|gi)\s?(.*)\s(ho|hp|cl|or)\s?(.*|bf1)\s(wt\d+\.?\d)\s?(.*)", msg, re.IGNORECASE)   
###groups = ('1198156435491265', 'TW', '01', '13.02.2011', 'GI', 'PM NP', 'HP', 'BF1', 'WT72.3', '')
#        nid = m.group(1)
#        twins = m.group(2)
#        number = m.group(3)
#        chidob = m.group(4)
#        sex = m.group(5)
#        ibibazo = m.group(6)
#        location = m.group(7)
#        bf1 = m.group(8)
#        weight = m.group(9)

    #Birth keyword
    @keyword("\s*bir(.*)")
    def birth(self, message, notice):
        """Birth report.  Sent when a new mother has a birth.  Can trigger alerts with particular action codes"""
        
        if not getattr(message, 'reporter', None):
            message.respond(_("You need to be registered first, use the REG keyword"))
            return True
            
        m = re.search("bir\s+(\d+)\s?(.*|tw|tr)\s([0-9]+)\s([0-9.]+)\s(bo|gi)\s?(.*)\s(ho|hp|cl|or)\s?(.*|bf1)\s(wt\d+\.?\d)\s?(.*)", message.text, re.IGNORECASE)
        if not m:
            message.respond(_("The correct format message is: BIR MOTHER_ID TWINS CHILD_NUM DOB SEX ACTION_CODE LOCATION_CODE BREASTFEEDING CHILD_WEIGHT"))
            return True

        nid = m.group(1)
        twins = m.group(2)
        number = m.group(3)
        chidob = m.group(4)
        sex = m.group(5)
        ibibazo = m.group(6)
        location = m.group(7)
        bf1 = m.group(8)
        weight = m.group(9)

        # get or create the patient
        patient = self.get_or_create_patient(message.reporter, nid)
        
        report = self.create_report('Birth', patient, message.reporter)
        
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
        if not report.has_dups():
        	report.save()
        else:
    		message.respond(_("This report has been recorded, and we cannot duplicate it again. Thank you!"))
    		return True
        
        # then associate all our fields with it
        fields.append(self.read_weight(weight, weight_is_mothers=False))
        fields.append(self.read_key(sex))
        fields.append(self.read_key(twins))
        fields.append(self.read_key(location))
        fields.append(self.read_key(bf1))

        for field in fields:
            field.save()
            report.fields.add(field)            
        
        # either send back the advice text or our default msg
        try:	response = self.run_triggers(message, report)
        except:	response = None
        if response:
            message.respond(response)
        else:
            message.respond(_("Thank you! Birth report submitted successfully."))
            
        # cc the supervisor if there is one
        try:	self.cc_supervisor(message, report)
   	except:	pass  
    	        
        return True
    
        #Birth keyword

