#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


##DJANGO LIBRARY
from django.utils.translation import ugettext as _
from django.utils.translation import activate, get_language
from decimal import *
from exceptions import Exception
import traceback
from datetime import *
from time import *
from django.db.models import Q

###DEVELOPED APPS
from rapidsmsrw1000.apps.ubuzima.reports.utils import *
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler


class BirHandler (KeywordHandler):
    """
    BIRTH REGISTRATION
    """

    keyword = "bir"
    
    def filter(self):
        if not getattr(message, 'connection', None):
            self.respond(_("You need to be registered first, use the REG keyword"))
            return True 
    def help(self):
        self.respond("The correct format message is: BIR MOTHER_ID CHILD_NUM DOB SEX ACTION_CODE LOCATION_CODE BREASTFEEDING CHILD_WEIGHT")

    def handle(self, text):
        #print self.msg.text
        return self.birth(self.msg)
        self.respond(text)

    def birth(self, message):

        try: activate(message.contact.language)
        except:    activate('rw')

        try:
            message.reporter = message_reporter(message)#Reporter.objects.filter(national_id = message.connection.contact.name )[0]
        except Exception, e:
            message.respond(_("You need to be registered first, use the REG keyword"))
            return True

        m = re.search("bir\s+(\d+)\s?(.*|tw|tr)\s([0-9]+)\s([0-9.]+)\s(bo|gi)\s?(.*)\s(ho|hp|cl|or)\s?(.*|bf1)\s(wt\d+\.?\d*)\s?(.*)", message.text, re.IGNORECASE)
        if not m:
            message.respond(_("The correct format message is: BIR MOTHER_ID CHILD_NUM DOB SEX ACTION_CODE LOCATION_CODE BREASTFEEDING CHILD_WEIGHT"))
            return True

        try:    nid = read_nid(message, m.group(1))
        except Exception, e:
            # there were invalid fields, respond and exit
            message.respond("%s" % e)
            return True
        twins = m.group(2)
        number = m.group(3)
        chidob = m.group(4)
        sex = m.group(5)
        ibibazo = m.group(6)
        location = m.group(7)
        bf1 = m.group(8)
        weight = m.group(9)

        # get or create the patient
        patient = get_or_create_patient(message.reporter, nid)
        
        report = create_report('Birth', patient, message.reporter)
    	        
        # read our fields
        try:
     	    
            (fields, dob) = read_fields(ibibazo, False, False)
    	    #print dob
    	    dob = parse_dob(chidob)
    	    
        except Exception, e:
            # there were invalid fields, respond and exit
            message.respond("%s" % e)
            return True

        # set the dob for the child if we got one
        if dob:
            report.set_date_string(dob)
            
        # set the child number
        child_num_type = FieldType.objects.get(key='child_number')
        fields.append(Field(type=child_num_type, value=Decimal(number)))

        # save the report
        for f in fields:
            if f.type in FieldType.objects.filter(category__name = 'Red Alert Codes'):
                message.respond(_("%(key)s:%(red)s is a red alert, please see how to report a red alert and try again.")\
                                         % { 'key': f.type.key,'red' : f.type.kw})
                return True

        for f in fields:
            if f.type in FieldType.objects.filter(category__name = 'Death Codes'):
                message.respond(_("%(key)s:%(dth)s is a death, please see how to report a death and try again.")\
                                         % { 'key': f.type.key,'dth' : f.type.kw})
                return True

        if not report.has_dups():
            report.set_pnc_edd_dates(report.date)            
            report.save()
        else:
    		message.respond(_("This report has been recorded, and we cannot duplicate it again. Thank you!"))
    		return True
        # then associate all our fields with it
        fields.append(read_weight(weight, weight_is_mothers=False))
        fields.append(read_key(sex))
        fields.append(read_key(twins))
        fields.append(read_key(location))
        fields.append(read_key(bf1))

        for field in fields:
            if field:
                field.report = report
                field.save()
                report.fields.add(field)  
    
        # either send back the advice text or our default msg
        try:	response = run_triggers(message, report)
        except:	response = None
        if response:
            message.respond(response)
        else:
            message.respond(_("Thank you! Birth report submitted successfully."))
            
        # cc the supervisor if there is one
        try:	cc_supervisor(message, report)
        except:	pass      
            	
        return True 

