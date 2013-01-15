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
from rapidsmsrw1000.apps.chws import models as confirm

class NdemeyeHandler (KeywordHandler):
    """
    CONFIRM REGISTRATION
    """

    keyword = "ndabyemeye"
    LANG = { 'en': 'English',
             'fr': 'French',
             'rw': 'Kinyarwanda' }
    
    def filter(self):
        if not getattr(message, 'connection', None):
            self.respond(_("You need to be registered first, use the REG keyword"))
            return True 
    def help(self):
        return self.ndemeye(self.msg)
        self.respond("The correct format message is: WHO")

    def handle(self, msg):
        #print self.msg.text
        return self.ndemeye(self.msg)
        self.respond(msg)

    def ndemeye(self, message):
        """Echos the last report that was sent for this report.  This is primarily used for unit testing"""

        try: activate(message.contact.language)
        except:    activate('rw')

        try:
            message.reporter = Reporter.objects.filter(connections__identity = message.connection.identity)[0]
        except Exception, e:
            message.respond(_("You need to be registered first, use the REG keyword"))
            return True

        if not getattr(message, 'reporter', None):
            message.respond(_("You need to be registered first, use the REG keyword"))
            return True

        try:
            cnf = confirm.RegistrationConfirmation.objects.filter(reporter__old_ref = message.reporter)
            if cnf.exists():
                cnf = cnf[0]
            else:
                chw = confirm.Reporter(national_id = message.reporter.alias, telephone_moh = message.connection.identity, old_ref = message.reporter)
                chw.save()
                cnf = confirm.RegistrationConfirmation(reporter = chw)
                cnf.received = datetime.now()
                cnf.responded = True
                cnf.answer = True
                cnf.save()
        except Exception, e:
            if message.reporter:
                message.respond("Muraho murakomeye! Ohereza ijambo 'WHO' urebeko wanditse neza. Murakoze")   
            else:   message.respond(_("You need to be registered first, use the REG keyword"))
            return True    			 

        message.respond("Muraho murakomeye! Mwatangira kohereza ubutumwa ku buzima bw'umubyeyi n'umwana kuri Rapidsms numero 1110.\
                             Ohereza ijambo 'WHO' urebeko wanditse neza. Murakoze")

        return True 
