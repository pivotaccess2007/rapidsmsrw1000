####SAMPLE MESSAGE #####
##res_EN = "The correct format message is: CHI MOTHER_ID CHILD_NUM DOB VACCINS VACCIN_SERIE ACTION_CODE LOCATION_CODE CHILD_WEIGHT MUAC"
##res_FR = "Andika: CHI INDANGAMUNTU IMPANGA NUMERO ITARIKI_AVUTSE IGITSINA IBIBAZO AHO_AVUKIYE KONKA IBIRO"
##msg = "CHI 1198156435491265 01 13.02.2011 V2 VI PM NP HP WT72.3 MUAC5.4"
###m = re.search("chi\s+(\d+)\s+([0-9]+)\s([0-9.]+)\s(v1|v2|v3|v4|v5|v6)\s(vc|vi)\s?(.*)\s(ho|hp|cl|or)\s(wt\d+\.?\d)\s(muac\d+\.?\d)\s?(.*)", msg, re.IGNORECASE)
##m = re.search("chi\s+(\d+)\s+([0-9]+)\s([0-9.]+)\s?(.*|v1|v2|v3|v4|v5|v6)\s?(.*|vc|vi)\s?(.*)\s(ho|hp|cl|or)\s(wt\d+\.?\d)\s(muac\d+\.?\d)\s?(.*)", msg, re.IGNORECASE)##for v ignored 
###groups = ('1198156435491265', 'TW', '01', '13.02.2011', 'GI', 'PM NP', 'HP', 'BF1', 'WT72.3', '')
#        nid = m.group(1)
#        number = m.group(2)
#        dob = m.group(3)
#        vaccins = m.group(4)
#        vaccin_serie = m.group(5)
#        ibibazo = m.group(6)
#        location = m.group(7)
#        weight = m.group(8)
#        muac = m.group(9)

    #Child Health keyword
    @keyword("\s*chi(.*)")
    def child(self, message, notice):
        """Child report.  Sent when a new mother has a birth.  Can trigger alerts with particular action codes"""
        
        if not getattr(message, 'reporter', None):
            message.respond(_("You need to be registered first, use the REG keyword"))
            return True
            
        m = re.search("chi\s+(\d+)\s+([0-9]+)\s([0-9.]+)\s(v1|v2|v3|v4|v5|v6)\s(vc|vi)\s?(.*)\s(ho|hp|cl|or)\s(wt\d+\.?\d)\s(muac\d+\.?\d)\s?(.*)", message.text, re.IGNORECASE)
        if not m:
            message.respond(_("The correct format message is: CHI MOTHER_ID CHILD_NUM DOB VACCINS VACCIN_SERIE ACTION_CODE LOCATION_CODE CHILD_WEIGHT MUAC"))
            return True

        nid = m.group(1)
        number = m.group(2)
        chidob = m.group(3)
        vaccins = m.group(4)
        vaccin_serie = m.group(5)
        ibibazo = m.group(6)
        location = m.group(7)
        weight = m.group(8)
        muac = m.group(9)

        # get or create the patient
        patient = self.get_or_create_patient(message.reporter, nid)
        
        report = self.create_report('Child Health', patient, message.reporter)
        
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
        fields.append(self.read_key(vaccins))
        fields.append(self.read_key(vaccin_serie))
        fields.append(self.read_key(location))
        fields.append(self.read_muac(muac))


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
    
        #Child Health keyword

