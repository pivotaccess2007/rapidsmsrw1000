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

class DepHandler (KeywordHandler):
    """
    Departure REGISTRATION
    """

    keyword = "dep"
    
    def filter(self):
        if not getattr(message, 'connection', None):
            self.respond(_("You need to be registered first, use the REG keyword"))
            return True 
    def help(self):
        self.respond("The correct format message is: DEP MOTHER_ID_OR_YOUR_PHONE_NUMBER_DATE_AS_DD_MM_YY  CHILD_NUMBER DOB")

    def handle(self, text):
        #print self.msg.text
        return self.dep(self.msg)
        self.respond(text)

    def dep(self, message):

    	try:
            message.reporter = PersistantConnection.objects.get(identity = message.connection.identity).reporter
        except Exception, e:
            message.respond(_("You need to be registered first, use the REG keyword"))
            return True

    	rez = re.match(r'dep\s+(\d+)\s?(.*)', message.text, re.IGNORECASE)
    	if not rez:
    	    message.respond(_('You never reported a departure. Departure are reported with the keyword DEP'))
    	    return True
        try:
            depid = read_nid(message, rez.group(1))
            dep = Departure(reporter = message.reporter, depid = depid)
            optional_part = rez.group(2)
            if optional_part:                
                optional_part = re.search(r'([0-9]+)\s+([0-9.]+)', optional_part, re.IGNORECASE)
                child_number = optional_part.group(1)
                dob = parse_dob(optional_part.group(2))
                dep.dob = set_date_string(dob)
                dep.child_number = child_number
    	    dep.save()
        except Exception, e:
            # there were invalid fields, respond and exit
            message.respond("%s" % e)
            return True
    	

        message.respond(_("Thank you! Dep report submitted successfully."))   
            	
        return True 

