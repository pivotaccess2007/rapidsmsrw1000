#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.core.management.base import BaseCommand
from rapidsmsrw1000.apps.ubuzima.models import Report, Reminder, ReminderType
from django.conf import settings
from rapidsmsrw1000.apps.reporters.models import Reporter
import urllib2
import time
import datetime
from optparse import make_option
from rapidsmsrw1000.apps.ubuzima.smser import *
import calendar
from django.utils import timezone

class Command(BaseCommand):
    help = "Checks and triggers all reminders.  This command should be run hourly via cron"
    option_list = BaseCommand.option_list + (
        make_option('-d', '--dry',
                    action='store_true',
                    dest='dry',
                    default=False,
                    help='Executes a dry run, doesnt send messages or update the db.'),
        )

    def send_message(self, connection, message):
        conf = {'kannel_host':'127.0.0.1', 'kannel_port':13013, 'kannel_password':'kannel', 'kannel_username':'kannel'}
        try:
            conf = settings.KANNEL_CONF
        except KeyError:
            pass
        
        url = "http://%s:%s/cgi-bin/sendsms?to=%s&text=%s&password=%s&user=%s" % (
            conf["kannel_host"], 
            conf["kannel_port"],
            urllib2.quote(connection.identity.strip()), 
            urllib2.quote(message),
            conf['kannel_password'],
            conf['kannel_username'])
        
        f = urllib2.urlopen(url, timeout=10)
        if f.getcode() / 100 != 2:
            print "Error delivering message to URL: %s" % url
            raise RuntimeError("Got bad response from router: %d" % f.getcode())

        # do things at a reasonable pace
        time.sleep(.2)


    def check_unresponded_red_alerts(self):
        try:
            today = timezone.localtime(timezone.now())#today = datetime.date.today()#test datetime.date(2012, 4, 12)
            sent = Report.objects.filter( type__name = "Red Alert", created__year = today.year, created__month = today.month ,\
                                        created__lte = timezone.localtime(timezone.now()) - datetime.timedelta(hours = 24))
            responded = Report.objects.filter( type__name = "Red Alert Result", created__year = today.year, created__month = today.month ,\
                         created__gte = timezone.localtime(timezone.now()) - datetime.timedelta(hours = 24))
            
            pending = sent.exclude(reporter__in = responded.values('reporter'), patient__in = responded.values('patient'), \
                            fields__type__key__in = responded.filter(fields__type__category__name__icontains = 'red').values('fields__type__key'))

            reminder_type = ReminderType.objects.get(name = "Red Alert Result")
            message = reminder_type.message_kw
            
            for alert in pending:                
                try:
                    if alert.reporter.language == 'en':	message = reminder_type.message_en
                    elif alert.reporter.language == 'fr':	message = reminder_type.message_fr
                    
                    message = message % (alert.patient.national_id)
                    
                    print "sending reminder to %s of '%s'" % (alert.reporter.connection().identity, message)#;print alert,message
                    if not self.dry:	self.send_message(alert.reporter.connection(), message)
                    
                except Exception, e:
                    print e
                    continue
            if not self.dry:	Reminder.objects.create(type=reminder_type, date=timezone.localtime(timezone.now()), reporter=alert.reporter)
        except Exception, e:
            print e
            pass

    def handle(self, **options):
        print "Running Schedules..."
        self.dry = options['dry']

        if self.dry:
            self.dry = True
            print "DRY RUN -- No messages will be sent, no database commits made."

        # We need to send reminders every two hours after a red alert was send, to ask whether the ambulance did com or not
        self.check_unresponded_red_alerts()

        print "Schedules complete."

        if self.dry:
            print "DRY RUN Complete."
