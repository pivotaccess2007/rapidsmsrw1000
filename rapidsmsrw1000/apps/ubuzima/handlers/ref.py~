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
from rapidsmsrw1000.apps.thousanddays.models import *

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

    	try:
            message.reporter = PersistantConnection.objects.get(identity = message.connection.identity).reporter
        except Exception, e:
            print e
        
    	rez = re.match(r'ref\s+(\d+)', message.text, re.IGNORECASE)
    	if not rez:
    	    message.respond(_('You never reported a refusal. Refusals are reported with the keyword REF'))
    	    return True
    	ref = Refusal(reporter = message.reporter, refid = rez.group(1))
    	ref.save()

        message.respond(_("Thank you! REF report submitted successfully."))
               	
        return True 

