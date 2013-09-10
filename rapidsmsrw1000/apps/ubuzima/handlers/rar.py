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


class RarHandler (KeywordHandler):
    """
    Red Alert Result report REGISTRATION
    """

    keyword = "rar"
    
    def filter(self):
        if not getattr(message, 'connection', None):
            self.respond(_("You need to be registered first, use the REG keyword"))
            return True 
    def help(self):
        self.respond("The correct format message is: RES MOTHER_ID REPORTED_SYMPTOMS LOCATION_CODE INTERVENTION_CODE MOTHER_STATUS CHILD_STATUS")

    def handle(self, text):
        #print self.msg.text
        return self.rar(self.msg)
        self.respond(text)

    def rar(self, message):

        try: activate(message.contact.language)
        except:    activate('rw')

    	try:
            message.reporter = message_reporter(message)#Reporter.objects.filter(national_id = message.connection.contact.name )[0]
        except Exception, e:
            message.respond(_("You need to be registered first, use the REG keyword"))
            return True

        m = re.search("rar\s+(\d+)\s?(.*)\s(ho|or)\s(pt|pr|tr|aa|al|at|na|ph)\s(mw|ms|cw|cs)s?(.*)", message.text, re.IGNORECASE)
        if not m:
            message.respond(_("The correct format message is: RAR MOTHER_ID REPORTED_SYMPTOMS LOCATION_CODE INTERVENTION_CODE MOTHER_STATUS CHILD_STATUS"))
            return True

        try:    nid = read_nid(message, m.group(1))
        except Exception, e:
            # there were invalid fields, respond and exit
            message.respond("%s" % e)
            return True
        ibibazo = m.group(2)
        location = m.group(3)
        intervention = m.group(4)
        mstatus = m.group(5)
        cstatus = m.group(6)

        # get or create the patient
        patient = get_or_create_patient(message.reporter, nid)

        report = create_report('Red Alert Result', patient, message.reporter)
        
        # Line below may be needed in case Risk reports are sent without previous Pregnancy reports
        #location = message.reporter.location
        
        # read our fields
        try:
            (fields, dob) = read_fields(ibibazo, False, True)
            
        
            fields.append(read_key(location))
            fields.append(read_key(intervention))
            fields.append(read_key(mstatus))
            for st in read_fields(cstatus, False, False)[0]:	fields.append(st)
  
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
        try:	response = None #run_triggers(message, report)
        except:	response = None
        if response:
            message.respond(response)
        else:
            message.respond(_("Thank you! Red Alert Result report submitted successfully."))
            
        # cc the supervisor if there is one
        try:	cc_supervisor(message, report)
        except:	pass      
            	
        return True 

