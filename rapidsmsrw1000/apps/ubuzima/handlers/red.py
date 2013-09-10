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


class RedHandler (KeywordHandler):
    """
    Red Alert report REGISTRATION
    """

    keyword = "red"
    
    def filter(self):
        if not getattr(message, 'connection', None):
            self.respond(_("You need to be registered first, use the REG keyword"))
            return True 
    def help(self):
        self.respond("The correct format message is: RED MOTHER_ID ACTION_CODE LOCATION_CODE MOTHER_WEIGHT")

    def handle(self, text):
        #print self.msg.text
        return self.red(self.msg)
        self.respond(text)

    def red(self, message):

        try: activate(message.contact.language)
        except:    activate('rw')

    	try:
            message.reporter = message_reporter(message)#Reporter.objects.filter(national_id = message.connection.contact.name )[0]
        except Exception, e:
            message.respond(_("You need to be registered first, use the REG keyword"))
            return True
        
        m = re.search("red\s+(\d+)\s?(.*)\s(ho|or)\s(wt\d+\.?\d*)\s?(.*)", message.text, re.IGNORECASE)
        if not m:
            message.respond(_("The correct format message is: RED MOTHER_ID ACTION_CODE LOCATION_CODE MOTHER_WEIGHT"))
            return True

        try:    nid = read_nid(message, m.group(1))
        except Exception, e:
            # there were invalid fields, respond and exit
            message.respond("%s" % e)
            return True
        ibibazo = m.group(2)
        location = m.group(3)
        weight = m.group(4)

        # get or create the patient
        patient = get_or_create_patient(message.reporter, nid)

        report = create_report('Red Alert', patient, message.reporter)
        
        # Line below may be needed in case Risk reports are sent without previous Pregnancy reports
        #location = message.reporter.location
        
        # read our fields
        try:
            (fields, dob) = read_fields(ibibazo, False, True)

            fields.append(read_weight(weight, weight_is_mothers=True))
            fields.append(read_key(location))

            is_red = check_is_red(fields)
            if is_red == False:
                message.respond(_("Invalid report syntax, please check to report this case."))
                return True

        except Exception, e:
            # there were invalid fields, respond and exit
            message.respond("%s" % e)
            return True

        # save the report
        for f in fields:
            if f.type in FieldType.objects.filter(category__name = 'Death Codes'):
                message.respond(_("%(key)s:%(dth)s is a death, please see how to report a death and try again.")\
                                         % { 'key': f.type.key,'dth' : f.type.kw})
                return True

        report.save()
        
	    # then associate all our fields with it
        for field in fields:
            if valid_red_field(field, report):
                field.report = report
                field.save()
                report.fields.add(field)

	    # either send back the advice text or our default msg
        try:	response = run_triggers(message, report)
        except:	response = None
        if response:
            message.respond(response)
        else:
            message.respond(_("Thank you! RED Alert report submitted successfully."))
            
        # cc the supervisor if there is one
        try:	cc_supervisor(message, report)
        except:	pass      
            	
        return True 

