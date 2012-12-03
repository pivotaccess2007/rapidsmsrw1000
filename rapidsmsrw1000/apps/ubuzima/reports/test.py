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

class TestHandler (KeywordHandler):
    """
    TEST REGISTRATION
    """

    keyword = "test"
    
    def filter(self):
        if not getattr(message, 'connection', None):
            self.respond(_("You need to be registered first, use the REG keyword"))
            return True 
    def help(self):
        self.respond("The correct format message is: TEST YOUR_NAME")

    def handle(self, text):
        #print self.msg.text
        return self.test_me(self.msg)
        self.respond(text)
	
    def test_me(self, msg):
        location_type, created = LocationType.objects.get_or_create(name = "Health Centre")
        location, created = Location.objects.get_or_create(name = "Muhoza", code = "F316", type = location_type)
        reporter, created = Reporter.objects.get_or_create(alias = "1198680069759062", village = "Muhoza", location = location)
        backend, created = PersistantBackend.objects.get_or_create(title = "kannel")
        connection, created = PersistantConnection.objects.get_or_create(backend = backend, identity = msg.connection.identity, reporter = reporter)
		
        msg.respond("HEY %s YOU ARE NOW REGISTERED TO RAPIDSMS TESTING ENV...YOU CAN START REPORTING" % msg.text)
        return True


###TEST CASE
#msg = "BIR 1198156435491265 TW 01 13.02.2011 GI PM NP HP BF1 WT72.3"
#from apps.thousanddays.reports.test import *
#x = Test()
#x.test_me(msg)
