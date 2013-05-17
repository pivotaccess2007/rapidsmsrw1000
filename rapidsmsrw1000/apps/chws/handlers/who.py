#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


##DJANGO LIBRARY
from django.utils.translation import ugettext as _
from django.utils.translation import activate, get_language

###DEVELOPED APPS
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsmsrw1000.apps.chws.models import Reporter, Supervisor

class WhoHandler (KeywordHandler):
    """
    VERIFY REGISTRATION
    """

    keyword = "who"
    LANG = { 'en': 'English',
             'fr': 'French',
             'rw': 'Kinyarwanda' }
    
    def filter(self):
        if not getattr(message, 'connection', None):
            self.respond(_("You need to be registered first"))
            return True 
    def help(self):
        return self.who(self.msg)
        self.respond("The correct format message is: WHO")

    def handle(self, msg):
        #print self.msg.text
        return self.who(self.msg)
        self.respond(msg)

    def who(self, message):
        """Returns what we know about the sender of this message.  This is used primarily for unit
           testing though it may prove usefu in the field"""
        try: activate(message.contact.language)
        except:    activate('rw')
        try:
            message.reporter = Reporter.objects.filter(national_id = message.connection.contact.name )[0]            
        except Exception, e:
            try:    message.supervisor = Supervisor.objects.filter(email = message.connection.contact.name )[0]
            except Exception,e:
                message.respond(_("You need to be registered first"))
                return True
           
        if getattr(message, 'reporter', None):
            if not message.reporter.role:
                message.respond(_("You are not in a group, located at %(location)s, you speak %(language)s") % \
                    { 'location': message.reporter.health_centre.name, 'language': self.LANG[message.reporter.language] } )          
            else:
                location = message.reporter.health_centre.name
                if message.reporter.village:
                    location += " (%s)" % message.reporter.village

                message.respond(_("You are a %(group)s, located at %(location)s, you speak %(language)s") % \
                    { 'group': message.reporter.role.name, 'location': location, 'language': self.LANG[message.reporter.language] } )

        elif getattr(message, 'supervisor', None):
            
            location = message.supervisor.health_centre.name if message.supervisor.health_centre else message.supervisor.referral_hospital.name
            if message.supervisor.village:
                location += " (%s)" % message.supervisor.village

            message.respond(_("You are a %(group)s, located at %(location)s, you speak %(language)s") % \
                { 'group': 'Supervisor', 'location': location, 'language': self.LANG[message.supervisor.language] } )
            
        else:
            message.respond(_("We don't recognize you"))
        return True
