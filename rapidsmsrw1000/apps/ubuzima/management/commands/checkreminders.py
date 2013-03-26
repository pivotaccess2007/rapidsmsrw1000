
from django.core.management.base import BaseCommand
from rapidsmsrw1000.apps.ubuzima.models import Report, Reminder, ReminderType
from django.conf import settings
from rapidsmsrw1000.apps.chws.models import Reporter, Supervisor
import urllib2
import time
import datetime
from optparse import make_option
from rapidsmsrw1000.apps.ubuzima.smser import *
import calendar
from django.utils import timezone

class Command(BaseCommand):
    help = "Checks and triggers all reminders.  This command should be run daily via cron"
    option_list = BaseCommand.option_list + (
        make_option('-d', '--dry',
                    action='store_true',
                    dest='dry',
                    default=False,
                    help='Executes a dry run, doesnt send messages or update the db.'),
        )

    cmd = Smser()

    def check_reminders(self, today, days, reminder_type, to_sup=False):
        try:
            # get the matching reminders
            pending = Report.get_reports_with_edd_in(today, days, reminder_type)

            # for each one, send a reminder
            for report in pending:
                if to_sup:
                    try:
                        print "supervisors of: %s" % report.reporter.telephone_moh
    
                        # look up the supervisors for the reporter's location
                        sups = Supervisor.objects.filter(health_centre = report.reporter.health_centre)
                        for sup in sups:
                            # determine the right messages to send for this reporter
                            message = reminder_type.message_kw
                            if sup.language == 'en':
                                message = reminder_type.message_en
                            elif sup.language == 'fr':
                                message = reminder_type.message_fr

                            message = message % report.patient.national_id

                            print "sending reminder to %s of '%s'" % (sup.telephone_moh, message)

                            # and send it off
                            if not self.dry:
                                try:	self.cmd.send_message_via_kannel(sup.telephone_moh, message)
				except:	pass
                    except Reporter.DoesNotExist:
                        pass

                else:
                    try:
                        message = reminder_type.message_kw
                        if report.reporter.language == 'en':
                            message = reminder_type.message_en
                        elif report.reporter.language == 'fr':
                            message = reminder_type.message_fr

                        message = message % report.patient.national_id

                        print "sending reminder to %s of '%s'" % (report.reporter.telephone_moh, message)
                        if not self.dry:
                            self.cmd.send_message_via_kannel(report.reporter.telephone_moh, message)
                    except Reporter.DoesNotExist:
                        pass

                if not self.dry:
                    report.reminders.create(type=reminder_type, location = report.location, date=datetime.datetime.now(), reporter=report.reporter)
        except Reporter.DoesNotExist:
            pass

    def check_pnc_reminders(self, today, days, reminder_type, to_sup=False, to_mother=False):
    	try:
	    	message, receivers = reminder_type.message_kw, []
	    	pending = Report.objects.filter(type__name = "Birth", date = today - datetime.timedelta(days = days), reminders = None)
	    	# for each one, send a reminder
	    	for report in pending:
	    		try:
		    		if to_sup:
		    			for x in Supervisor.objects.filter(health_centre = report.location):
		    				receivers.append(x)
		    		else:	receivers.append(report.reporter)
	     			for reporter in receivers:
	    				if reporter.language == 'en':
	    					message = reminder_type.message_en
	    				elif reporter.language == 'fr':
	    					message = reminder_type.message_fr
	    				message = message % (report.patient.national_id,report.date_string)
	    				print "sending reminder to %s of '%s'" % (report.reporter.telephone_moh, message)
	    				if not self.dry:	self.cmd.send_message_via_kannel(report.reporter.telephone_moh, message)
	     			
	     		except :	continue
    			if not self.dry:	report.reminders.create(type=reminder_type,location = report.location, date=datetime.datetime.now(), reporter=report.reporter)
	    		if to_mother:
	    			if not self.dry:
	    				if report.patient.telephone:	self.cmd.send_message_via_kannel(report.patient.telephone, message % (report.patient.national_id,report.date_string))
    	except:	pass


    def check_unresponded_risks(self):
        try:
            today = timezone.localtime(timezone.now())#today = datetime.date.today()#test datetime.date(2012, 4, 12)
            sent = Report.objects.filter( type__name = "Risk", created__year = today.year, created__month = today.month ,\
                                        created__lte = timezone.localtime(timezone.now()) - datetime.timedelta(days = 7))
            responded = Report.objects.filter( type__name = "Risk Result", created__year = today.year, created__month = today.month ,\
                         created__gte = timezone.localtime(timezone.now()) - datetime.timedelta(days = 7))
            
            pending = sent.exclude(reporter__in = responded.values('reporter'), patient__in = responded.values('patient'), \
                            fields__type__key__in = responded.filter(fields__type__category__name__icontains = 'risk').values('fields__type__key'))

            reminder_type = ReminderType.objects.get(name = "Risk Result")
            message = reminder_type.message_kw
            #print responded.count()
            for alert in pending:                
                try:
                    if alert.reporter.language == 'en':	message = reminder_type.message_en
                    elif alert.reporter.language == 'fr':	message = reminder_type.message_fr
                    
                    msg = message % (alert.patient.national_id)
                    
                    print "sending reminder to %s of '%s'" % (alert.reporter.telephone_moh, msg)
                    if not self.dry:	self.cmd.send_message_via_kannel(alert.reporter.telephone_moh, msg)
                    
                except Exception, e:
                    print e
                    continue
            	if not self.dry:	alert.reminders.create(type=reminder_type,location = alert.reporter.health_centre, date=timezone.localtime(timezone.now()), reporter=alert.reporter)
        except Exception, e:
            print e
            pass

    def check_unresponded_ccm(self):
        try:
            today = timezone.localtime(timezone.now())#today = datetime.date.today()#test datetime.date(2012, 4, 12)
            sent = Report.objects.filter( type__name = "Community Case Management", created__year = today.year, created__month = today.month ,\
                                        created__lte = timezone.localtime(timezone.now()) - datetime.timedelta(days = 4))
            responded = Report.objects.filter( type__name = "Case Management Response", created__year = today.year, created__month = today.month ,\
                         created__gte = timezone.localtime(timezone.now()) - datetime.timedelta(days = 4))
            
            pending = sent.exclude(reporter__in = responded.values('reporter'), patient__in = responded.values('patient'), \
                            fields__type__key__in = responded.filter(fields__type__category__name__icontains = 'risk').values('fields__type__key'))

            reminder_type = ReminderType.objects.get(name = "Case Management Response")
            message = reminder_type.message_kw
            #print sent.count()
            for alert in pending:                
                try:
                    if alert.reporter.language == 'en':	message = reminder_type.message_en
                    elif alert.reporter.language == 'fr':	message = reminder_type.message_fr
                    
                    msg = message % alert.patient.national_id
                    
                    print "sending reminder to %s of '%s'" % (alert.reporter.telephone_moh, msg)
                    if not self.dry:	self.cmd.send_message_via_kannel(alert.reporter.telephone_moh, msg)
                    
                except Exception, e:
                    print e
                    continue
            	if not self.dry:	alert.reminders.create(type=reminder_type,location = alert.reporter.health_centre, date=timezone.localtime(timezone.now()), reporter=alert.reporter)
        except Exception, e:
            print e
            pass
    

    def check_feedback(self):
    	try:
	    	reporters = Reporter.objects.all()
	    	
	    	for reporter in reporters:
	    		try:
   				reminder_type = ReminderType.objects.get(name = 'Active Reporter Feedback')
    				message = reminder_type.message_kw
    				message = message % Report.objects.filter(reporter=reporter, created__month = datetime.date.today\
									().month, created__year = datetime.date.today().year).count()
	    			if reporter.last_seen().date() < datetime.date.today() - datetime.timedelta(days=30):
	    				reminder_type = ReminderType.objects.get(name = 'Inactive Reporter Feedback')
    					message = reminder_type.message_kw
	   				if reporter.language == 'en':	message = reminder_type.message_en
	    				elif reporter.language == 'fr':	message = reminder_type.message_fr
	    			print "notifying %s with '%s'" % (reporter.telephone_moh, message)	
	   			if not self.dry:	self.cmd.send_message_via_kannel(reporter.telephone_moh, message)
	    		except:	continue

	    		if not self.dry:	Reminder.objects.create(type=reminder_type,location = reporter.health_centre, date=datetime.datetime.now(), reporter=reporter)
    	
    	except:	pass	
    	

    def check_expired_reporters(self):
        # get our reminder
        reminder_type = ReminderType.objects.get(name = "Inactive Reporter")
        today = timezone.localtime(timezone.now())#datetime.date.today()

        # get all our pending expired reporters
        for reporter in Reminder.get_expired_reporters(today):
            # look up the supervisors for this reporter
            sups = Supervisor.objects.filter(health_centre=reporter.health_centre)
            for sup in sups:
                # determine the right messages to send for this reporter
                message = reminder_type.message_kw
                if sup.language == 'en':
                    message = reminder_type.message_en
                elif sup.language == 'fr':
                    message = reminder_type.message_fr
                    
                message = message % (reporter.national_id, reporter.telephone_moh)

                print "notifying %s of expired reporter with '%s'" % (sup.telephone_moh, message)
                #print reporter.last_seen()
                
                # and send it off
                if not self.dry:
                    try:	self.cmd.send_message_via_kannel(sup.telephone_moh, message)
   	   	    except:	pass

            if not self.dry:
                try:	Reminder.objects.create(type=reminder_type, date=datetime.datetime.now(), reporter=reporter, location = reporter.health_centre)
		except:	pass

    def handle(self, **options):
        print "Running reminders.."

        self.dry = options['dry']

        if self.dry:
            self.dry = True
            print "DRY RUN -- No messages will be sent, no database commits made."

        # today
        today = timezone.localtime(timezone.now())#datetime.date.today()

        # ANC2
        reminder_type = ReminderType.objects.get(name = '2nd ANC Visit')
        self.check_reminders(today, Report.DAYS_ANC2, reminder_type)

        # ANC3
        reminder_type = ReminderType.objects.get(name = '3rd ANC Visit')
        self.check_reminders(today, Report.DAYS_ANC3, reminder_type)

        # ANC4
        reminder_type = ReminderType.objects.get(name = '4th ANC Visit')
        self.check_reminders(today, Report.DAYS_ANC4, reminder_type)

        # EDD
        reminder_type = ReminderType.objects.get(name = 'Week Before Expected Delivery Date')
        self.check_reminders(today, Report.DAYS_EDD, reminder_type)

        # On the due date (Revence)
        reminder_type = ReminderType.objects.get(name = 'Due Date')
        self.check_reminders(today, Report.DAYS_ON_THE_DOT, reminder_type)

        # Seven days after due date (Revence)
        reminder_type = ReminderType.objects.get(name = 'Week After Due Date')
        self.check_reminders(today, Report.DAYS_WEEK_LATER, reminder_type)

    	# Two days after Birth date
        reminder_type = ReminderType.objects.get(name = 'PNC visit after 2 days of Delivery Date')
        self.check_pnc_reminders(today, Report.DAYS_PNC1, reminder_type,to_sup=True,to_mother=True)
    	
    	# Six days after Birth date
        reminder_type = ReminderType.objects.get(name = 'PNC visit after 6 days of Delivery Date')
        self.check_pnc_reminders(today, Report.DAYS_PNC2, reminder_type,to_sup=True,to_mother=True)

    	# 28 days after Birth date
        reminder_type = ReminderType.objects.get(name = 'PNC visit after 28 days of Delivery Date')
        self.check_pnc_reminders(today, Report.DAYS_PNC3, reminder_type,to_sup=True,to_mother=True)

    	# 6 months after Birth date
        reminder_type = ReminderType.objects.get(name = 'Child Health after 6 months of Delivery Date')
        self.check_pnc_reminders(today, Report.DAYS_MONTH6, reminder_type,to_sup=True,to_mother=True)

   	# 9 months after Birth date
        reminder_type = ReminderType.objects.get(name = 'Child Health after 9 months of Delivery Date')
        self.check_pnc_reminders(today, Report.DAYS_MONTH9, reminder_type,to_sup=True,to_mother=True)

   	# 18 months after Birth date
        reminder_type = ReminderType.objects.get(name = 'Child Health after 18 months of Delivery Date')
        self.check_pnc_reminders(today, Report.DAYS_MONTH18, reminder_type,to_sup=True,to_mother=True)

    	# 24 months after Birth date
        reminder_type = ReminderType.objects.get(name = 'Child Health after 24 months of Delivery Date')
        self.check_pnc_reminders(today, Report.DAYS_MONTH24, reminder_type,to_sup=True,to_mother=True)

        # EDD for SUPs
        reminder_type = ReminderType.objects.get(name = 'Two Weeks Before Expected Delivery Date')
        self.check_reminders(today, Report.DAYS_SUP_EDD, reminder_type, to_sup=True)

        # RISKS RESULTS REMINDERS
        self.check_unresponded_risks()

        # CCM RESULTS REMINDERS
        self.check_unresponded_ccm()
   	
    	#Send monthly performance feedback messages
   	if calendar.monthrange(today.year,today.month)[1] == today.day:	self.check_feedback()

        # Finally look for any reports who need reminders
        #self.check_expired_reporters()

        print "Complete."

        if self.dry:
            print "DRY RUN Complete."







####VACCINATION REMINDERS ### TO DO WHEN THE SCHEDULE IS DEFINED ####
