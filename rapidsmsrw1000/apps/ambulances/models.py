#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.db import models
from rapidsmsrw1000.apps.chws.models import *
from rapidsms.router import send
from rapidsms.models import Connection

def forward (message, identity, text):
    
    if message.connection:
        conn = Connection(backend = message.connection.backend, identity = identity)        
        send( text, conn)
        #print conn, text     
        return True
    else:
        return False

class AmbulanceDriver(models.Model):
    phonenumber = models.CharField(max_length = 20)
    name 	= models.CharField(max_length = 100)
    identity    = models.CharField(max_length = 20)
    health_centre	= models.ForeignKey(HealthCentre, related_name = 'driver_hc', null =True)
    referral_hospital	= models.ForeignKey(Hospital, related_name = 'driver_hospital', null = True)
    district = models.ForeignKey(District, related_name = 'driver_district')

    def send_notification(self, message, report):
        '''Assume that the report that came in message is scary, and needs ambulance attention _aussit^ot_. It notifies supervisors about the registration numbers of the ambulance (self) being dispatched, and tells the ambulance driver(s) about the case, the reporting CHW's number, and the location.'''

        hwmsg  = 'An ambulance driver (%s) has been notified.' % (str(self.phonenumber))
        drvmsg = 'Umujyanama w\'ubuzima ukoresha telephoni %s yohereje ubutumwa ku kigo nderabuzima cya %s ko ashobora kuba akeneneye ubufasha bwa ambilansi.'\
                         % (str(report.reporter.connection().identity), str(report.location.name))

        forward(message, self.phonenumber, drvmsg)

        return hwmsg

    class Meta:
        
        # define a permission for this app to use the @permission_required
        # in the admin's auth section, we have a group called 'manager' whose
        # users have this permission -- and are able to see this section
        permissions = (
            ("can_view", "Can view"),
        ) 
        unique_together = ("phonenumber", "health_centre")
        unique_together = ("phonenumber", "referral_hospital")

    def __unicode__(self):
        return u'%s (%s): %s' % (str(self.name), str(self.identity), str(self.phonenumber))

class Ambulance(models.Model):
    '''Record an ambulance, drivers' numbers, and the location where it is found. That way, ambulance dispatches can be done well.'''

    drivers = models.ForeignKey(AmbulanceDriver, related_name = 'conducteur')
    plates  = models.CharField(max_length = 10)
    health_centre	= models.ForeignKey(HealthCentre, related_name = 'ambulance_hc', null =True)
    referral_hospital	= models.ForeignKey(Hospital, related_name = 'ambulance_hospital', null = True)
    district = models.ForeignKey(District, related_name = 'ambulance_district')

    class Meta:
        
        # define a permission for this app to use the @permission_required
        # in the admin's auth section, we have a group called 'manager' whose
        # users have this permission -- and are able to see this section
        permissions = (
            ("can_view", "Can view"),
        ) 

    def __unicode__(self):
        return '%s (%s) @ %s' % (str(self.plates), str(self.plates[0]), str(self.station))

    def __int__(self):
        return self.id
