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


class RefHandler (KeywordHandler):
    """
    Refusal report REGISTRATION
    """

    keyword = "ref"
    
    def filter(self):
        if not getattr(message, 'connection', None):
            self.respond(_("You need to be registered first, use the REG keyword"))
            return True 
    def help(self):
        self.respond("The correct format message is: REF MOTHER_ID_OR_YOUR_PHONE_NUMBER_DATE_AS_DD_MM_YY ")

    def handle(self, text):
        #print self.msg.text
        return self.ref(self.msg)
        self.respond(text)

    def ref(self, message):

        try: activate(message.contact.language)
        except:    activate('rw')

    	try:
            message.reporter = message_reporter(message)#Reporter.objects.filter(national_id = message.connection.contact.name )[0]
        except Exception, e:
            message.respond(_("You need to be registered first, use the REG keyword"))
            return True
        
    	rez = re.match(r'ref\s+(\d+)', message.text, re.IGNORECASE)
    	if not rez:
    	    message.respond(_('You never reported a refusal. Refusals are reported with the keyword REF'))
    	    return True
        try:    refid = read_nid(message, rez.group(1))
        except Exception, e:
            # there were invalid fields, respond and exit
            message.respond("%s" % e)
            return True
        # get or create the patient
        patient = get_or_create_patient(message.reporter, refid)
        
        report = create_report('Refusal', patient, message.reporter)
    	report.save()

        message.respond(_("Thank you! REF report submitted successfully."))
               	
        return True 

