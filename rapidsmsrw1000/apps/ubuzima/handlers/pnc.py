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


class PncHandler (KeywordHandler):
    """
    Post Natal Care report REGISTRATION
    """

    keyword = "pnc"
    
    def filter(self):
        if not getattr(message, 'connection', None):
            self.respond(_("You need to be registered first, use the REG keyword"))
            return True 
    def help(self):
        self.respond("The correct format message is: PNC MOTHER_ID PNC_ROUND DOB SYMPTOMS INTERVENTION CHILD_STATUS")

    def handle(self, text):
        #print self.msg.text
        return self.pnc(self.msg)
        self.respond(text)

    def pnc(self, message):

        try: activate(message.contact.language)
        except:    activate('rw')

    	try:
            message.reporter = message_reporter(message)#Reporter.objects.filter(national_id = message.connection.contact.name )[0]
        except Exception, e:
            message.respond(_("You need to be registered first, use the REG keyword"))
            return True

        m = re.search("pnc\s+(\d+)\s+(pnc1|pnc2|pnc3)\s([0-9.]+)\s?(.*)\s(pt|pr|tr|aa|al|at|na|ph)\s(mw|ms|cw|cs)\s?(.*)", message.text, re.IGNORECASE)
        if not m:
            message.respond(_("The correct format message is: PNC MOTHER_ID PNC_ROUND DOB SYMPTOMS INTERVENTION CHILD_STATUS"))
            return True

        try:    nid = read_nid(message, m.group(1))
        except Exception, e:
            # there were invalid fields, respond and exit
            message.respond("%s" % e)
            return True
        tour = m.group(2)
        chidob = m.group(3)
        ibibazo = m.group(4)
        intervention = m.group(5)
        mstatus = m.group(6)
        cstatus = m.group(7)

        # get or create the patient
        patient = get_or_create_patient(message.reporter, nid)
        
        report = create_report('PNC', patient, message.reporter)
        
        # read our fields
        try:
            (fields, dob) = read_fields(ibibazo, False, False)
    	    dob = parse_dob(chidob)
        except Exception, e:
            # there were invalid fields, respond and exit
            message.respond("%s" % e)
            return True

        # set the dob for the child if we got one
        if dob:
            report.set_date_string(dob)
            
        
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

        report.save()
                
        # then associate all our fields with it
        
        fields.append(read_key(tour))
        for st in read_fields(cstatus, False, False)[0]:	fields.append(st)
        fields.append(read_key(mstatus))
        fields.append(read_key(intervention))

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
            message.respond(_("Thank you! PNC report submitted successfully."))
            
        # cc the supervisor if there is one
        try:	cc_supervisor(message, report)
        except:	pass      
            	
        return True 

