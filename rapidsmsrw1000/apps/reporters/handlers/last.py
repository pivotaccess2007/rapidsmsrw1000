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

class LastHandler (KeywordHandler):
    """
    LAST REPORT
    """

    keyword = "last"
    LANG = { 'en': 'English',
             'fr': 'French',
             'rw': 'Kinyarwanda' }
    
    def filter(self):
        if not getattr(message, 'connection', None):
            self.respond(_("You need to be registered first, use the REG keyword"))
            return True 
    def help(self):
        return self.last(self.msg)
        self.respond("The correct format message is: WHO")

    def handle(self, msg):
        #print self.msg.text
        return self.last(self.msg)
        self.respond(msg)

    def last(self, message):
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
    
        reports = Report.objects.filter(reporter=message.reporter).order_by('-pk')
    
        if not reports:
            message.respond(_("You have not yet sent a report."))
            return True
    
        report = reports[0]
        
        fields = []
        for field in report.fields.all().order_by('type'):
            fields.append(unicode(field))
            
        dob = _(" Date: %(date)s") % { 'date': report.date_string } if report.date_string else ""
        
        message.respond(report.as_verbose_string())
    	      
        return True 
