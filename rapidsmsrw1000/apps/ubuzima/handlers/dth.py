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


class DthHandler (KeywordHandler):
    """
    Death REGISTRATION
    """

    keyword = "dth"
    
    def filter(self):
        if not getattr(message, 'connection', None):
            self.respond(_("You need to be registered first, use the REG keyword"))
            return True 
    def help(self):
        self.respond("The correct format message is: DTH MOTHER_ID CHILD_NUMBER DATE_OF_BIRTH DEATH_CODE")

    def handle(self, text):
        #print self.msg.text
        return self.death(self.msg)
        self.respond(text)

    def death(self, message):

        try: activate(message.contact.language)
        except:    activate('rw')

    	try:
            message.reporter = message_reporter(message)#Reporter.objects.filter(national_id = message.connection.contact.name )[0]
        except Exception, e:
            message.respond(_("You need to be registered first, use the REG keyword"))
            return True

        m = re.search("dth\s+(\d+)\s([0-9]+)\s([0-9.]+)\s(hp|cl|or|ho)\s(nd|cd|md)\s?(.*)", message.text, re.IGNORECASE)
        
        if not m:
            message.respond(_("The correct format message is: DTH MOTHER_ID CHILD_NUMBER DATE_OF_BIRTH DEATH_CODE"))
            return True

        try:    nid = read_nid(message, m.group(1))
        except Exception, e:
            # there were invalid fields, respond and exit
            message.respond("%s" % e)
            return True

        number = m.group(2)
        chidob = m.group(3)
        location = m.group(4)
        death = m.group(5)

        ibibazo = "%s %s" % ( location, death)            
            
        # get or create the patient
        patient = get_or_create_patient(message.reporter, nid)

        report = create_report('Death', patient, message.reporter)
        
        # Line below may be needed in case Risk reports are sent without previous Pregnancy reports
        #location = message.reporter.location
        
        # read our fields
        try:
            (fields, dob) = read_fields(ibibazo, False, False)
    	    if chidob:  dob = parse_dob(chidob)
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
        if not report.has_dups():
        	report.save()
        else:
    		message.respond(_("This report has been recorded, and we cannot duplicate it again. Thank you!"))
    		return True
        

	    # then associate all our fields with it
        
        if number:  fields.append(read_number(number))
        
        for field in fields:
            if field:
                try:
                    if field.type.key == 'cd' and (d.created.date() - d.date).days < 42: field.type = FieldType.objects.get(key = 'nd')
                except:
                    pass
                field.report = report
                field.save()
                report.fields.add(field)

	    # either send back the advice text or our default msg
        try:	response = run_triggers(message, report)
        except:	response = None
        if response:
            message.respond(response)
        else:
            message.respond(_("Thank you! Death report submitted successfully."))
            
        # cc the supervisor if there is one
        try:	cc_supervisor(message, report)
        except:	pass      
            	
        return True 

