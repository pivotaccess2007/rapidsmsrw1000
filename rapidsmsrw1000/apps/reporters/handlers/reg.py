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
from django.conf import settings
from rapidsms.models import Contact

class RegHandler (KeywordHandler):
    """
    CHW REGISTRATION
    """

    keyword = "reg|sup"
    
    def filter(self):
        if not getattr(message, 'connection', None):
            self.respond(_("You need to be registered first, use the REG keyword"))
            return True 
    def help(self):
        self.respond("The correct format message is: REG YOUR_ID CLINIC_ID LANG VILLAGE")

    def handle(self, text):
        #print self.msg.text
        return self.sup_or_reg(self.msg)
        self.respond(text)

    def sup_or_reg(self, message):
        """Handles both incoming REG and SUP commands, creating the appropriate Reporter object, 
           stashing away the attributes and making the connection with this phone number. """
          
        self.debug("SUP message: %s" % message.text)
        m = re.search("^\s*(\w+)\s+(\d+)\s+(\d+)(.*)$", message.text, re.IGNORECASE)
        if not m:
            # give appropriate error message based on the incoming message type
            if message.text.strip()[:3].upper() == 'SUP':
                message.respond(_("The correct message format is: SUP YOUR_ID CLINIC_ID LANG VILLAGE"))
            else:
                message.respond(_("The correct message format is: REG YOUR_ID CLINIC_ID LANG VILLAGE"))
            return True

        received_nat_id = m.group(2)
        
        if len(received_nat_id) != 16:
            message.respond(_("Error.  National ID must be exactly 16 digits, you sent the id: %(nat_id)s") % 
                            { "nat_id": received_nat_id } )
            return True
        
        received_clinic_id = m.group(3)
        optional_part = m.group(4)
        
        # do we already have a report for our connection?
        # if so, just update it
        
        if not getattr(message, 'reporter', None):
            if settings.TRAINING_ENV == True:
                rep, created = Reporter.objects.get_or_create(alias=received_nat_id)
                message.reporter = rep
            else:
                try:
                    rep = Reporter.objects.get(alias=received_nat_id)
                    message.reporter = rep
                except Reporter.DoesNotExist:
                    message.respond(_("Please contact your Health Centre to register your National ID"))
                    return True
            
            # connect this reporter to the connection
            contact, created = Contact.objects.get_or_create(name = rep.alias)
            contact.language = rep.language.lower()
            contact.save()
            message.connection.contact = contact
            message.connection.save()

            backend, created = PersistantBackend.objects.get_or_create(title = "kannel")
            message.persistant_connection, created = PersistantConnection.objects.get_or_create(backend = backend, identity=message.connection.identity)
            message.persistant_connection.reporter = message.reporter
            message.persistant_connection.save()
         
        
        # read our clinic
        clinic = Location.objects.filter(code=fosa_to_code(received_clinic_id))
        
        # not found?  That's an error
        if not clinic:
            message.respond(_("Unknown Health Clinic ID: %(clinic)s") % \
                            { "clinic": received_clinic_id})
            return True
        
        clinic = clinic[0]
        
        # set the location for this reporter
        message.reporter.location = clinic
        
        # set the group for this reporter based on the incoming keyword
        group_title = 'Supervisor' if (message.text.strip()[:3].lower() == 'sup') else 'CHW' 
        
        group = ReporterGroup.objects.get(title=group_title)
        message.reporter.groups.add(group)
        
        m2 = re.search("(\s*)(fr|en|rw)(\s*)", optional_part, re.IGNORECASE)
    
        lang = "rw"
        if m2:
            lang = m2.group(2).lower()
                        
            # build our new optional part, which is just the remaining stuff
            optional_part = ("%s %s" % (m2.group(1), m2.group(3))).strip()

        # save away the language
        message.reporter.language = lang
        message.connection.contact.language = lang
        message.connection.contact.save()
        # and activate it
        activate(lang)

        # if we actually have remaining text, then save that away as our village name
        if optional_part:
            message.reporter.village = optional_part
            
        # save everything away
        message.reporter.save()
        
        message.respond(_("Thank you for registering at %(clinic)s") % \
                        { 'clinic': clinic.name } )
        
        return True
