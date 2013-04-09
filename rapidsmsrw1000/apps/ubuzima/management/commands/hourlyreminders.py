#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.core.management.base import BaseCommand
from rapidsmsrw1000.apps.ubuzima.models import Report, Reminder, ReminderType
from django.conf import settings
from rapidsmsrw1000.apps.chws.models import Reporter
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

    cmd = Smser()


    def check_unresponded_red_alerts(self):
        try:
            today = timezone.localtime(timezone.now())#today = datetime.date.today()#test datetime.date(2012, 4, 12)
            sent = Report.objects.filter( type__name = "Red Alert", created__gte = today - datetime.timedelta(hours = 24))#sent = Report.objects.filter( type__name = "Red Alert", created__year = today.year, created__month = today.month ,\
                                        #created__lte = timezone.localtime(timezone.now()) - datetime.timedelta(hours = 24))
            responded = Report.objects.filter( type__name = "Red Alert Result",created__gte = today - datetime.timedelta(hours = 24))#responded = Report.objects.filter( type__name = "Red Alert Result", created__year = today.year, created__month = today.month ,\
                         #created__gte = timezone.localtime(timezone.now()) - datetime.timedelta(hours = 24))
            
            pending = sent.exclude(reporter__in = responded.values('reporter'), patient__in = responded.values('patient'), \
                            fields__type__key__in = responded.filter(fields__type__category__name__icontains = 'red').values('fields__type__key'))

            reminder_type = ReminderType.objects.get(name = "Red Alert Result")
            message = reminder_type.message_kw
            
            for alert in pending:
                reminders = Reminder.objects.filter(reporter = alert.reporter, type=reminder_type, date__gte = today - datetime.timedelta(hours = 24)).order_by('-date')
                if reminders : continue             
                try:
                    
                    if alert.reporter.language == 'en':	message = reminder_type.message_en
                    elif alert.reporter.language == 'fr':	message = reminder_type.message_fr
                    
                    message = message % (alert.patient.national_id)
                    
                    print "sending reminder to %s of '%s'" % (alert.reporter.telephone_moh, message)#;print alert,message
                    if not self.dry:	self.cmd.send_message_via_kannel(alert.reporter.telephone_moh, message)
                    
                except Exception, e:
                    print e
                    continue
                if not self.dry:	alert.reminders.create(type=reminder_type, location = alert.location,  date=timezone.localtime(timezone.now()), reporter=alert.reporter)
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
