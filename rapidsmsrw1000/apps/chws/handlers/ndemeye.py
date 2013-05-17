#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


##DJANGO LIBRARY
from django.utils.translation import ugettext as _
from django.utils.translation import activate, get_language

from exceptions import Exception
import traceback
from datetime import *
from time import *

###DEVELOPED APPS
from django.conf import settings
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsmsrw1000.apps.chws.models import RegistrationConfirmation, Reporter, Supervisor

class NdemeyeHandler (KeywordHandler):
    """
    CONFIRM REGISTRATION
    """

    keyword = "ndabyemeye|ndemeye"
    LANG = { 'en': 'English',
             'fr': 'French',
             'rw': 'Kinyarwanda' }
    
    def filter(self):
        if not getattr(message, 'connection', None):
            self.respond(_("You need to be registered first"))
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
            message.reporter = Reporter.objects.filter(national_id = message.connection.contact.name )[0]
        except Exception, e:
            try:    message.supervisor = Supervisor.objects.filter(email = message.connection.contact.name )[0]
            except Exception,e:
                message.respond(_("You need to be registered first"))
                return True

        try:
            cnf = RegistrationConfirmation.objects.get(reporter = message.reporter)
            cnf.received = datetime.now()
            cnf.responded = True
            cnf.answer = True
            cnf.save()
        except Exception, e:
            if message.supervisor:
                message.respond("Muraho murakomeye! Ohereza ijambo 'WHO' urebeko wanditse neza, kandi wibutse abajyanamako bagomba kohereza ubutumwa kuri %s. Murakoze" % settings.SHORTCODE)   
            else:   message.respond(_("You need to be registered first"))
            return True    			 

        message.respond("Muraho murakomeye! Mwatangira kohereza ubutumwa ku buzima bw'umubyeyi n'umwana kuri Rapidsms numero %s.\
                             Ohereza ijambo 'WHO' urebeko wanditse neza. Murakoze" % settings.SHORTCODE)

        return True 
