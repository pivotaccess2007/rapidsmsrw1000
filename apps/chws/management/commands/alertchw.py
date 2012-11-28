from django.core.management.base import BaseCommand
from optparse import make_option
from django.conf import settings
import os
from chws.views import *

import urllib2
import time
import datetime
from apps.logger.models import *


class Command(BaseCommand):
    help = "Checks and triggers all start alerts.  This command should be run daily via cron"
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
            conf = settings.RAPIDSMS_APPS["kannel"]
        except KeyError:
            pass
    	try:
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
    	except:	pass

    def check_alerts(self, to_sup=False):
        try:
            # get the matching alerts
            pending = RegistrationConfirmation.objects.filter(sent = None)
	    message = 'Kuri Supervisor wa CHWs, Minisisteri y\'Ubuzima yakwemeje muri gahunda ya Rapidsms. Niba ubyemeye, \
			subiza wohereza ijambo  "Ndabyemeye" kuri 1110.'
            # for each one, send a alert to start
	    count = 0
            for cnf in pending:
		count = count + 1
		try:	print cnf.reporter.role.code
    	    	except:	continue
                if to_sup:
                    try:
                        print count, "Supervisor of : %s" % cnf.reporter.national_id
    
                        # look up the supervisors for the reporter's location
                        sups = old_registry.Reporter.objects.filter(location = get_reporter(cnf.reporter.national_id).location, groups__pk=2)
                        for sup in sups:
                            # determine the right messages to send for this reporter
			    
                            message_kw = 'Kuri Supervisor wa CHWs, Minisisteri y\'Ubuzima yakwemeje muri gahunda ya Rapidsms. \
						Niba ubyemeye, subiza wohereza ijambo  "Ndabyemeye" kuri 1110.'
                            if sup.language == 'EN':
                                message = message_kw
                            elif sup.language == 'FR':
                                message = message_kw

                            message = message_kw 

                            print "sending alert to %s of '%s'" % (sup.connection().identity, message)

                            # and send it off
                            if not self.dry:
                                self.send_message(sup.connection(), message)
                                cnf.sent = datetime.datetime.now()
                                cnf.responded = False
                                cnf.answer = False
                                cnf.save()
                    except Reporter.DoesNotExist:
                        pass

                if cnf.reporter.role.code == 'asm':
                    try:
                        message_kw = 'Kuri ASM, Minisisteri y\'Ubuzima yakwemeje muri gahunda ya Rapidsms. Niba ubyemeye, subiza wohereza ijambo \
						 "Ndabyemeye" kuri 1110.'
                        if cnf.reporter.language == 'EN':
                            message = message_kw
                        elif cnf.reporter.language == 'FR':
                            message = message_kw

                        message = message_kw

                        print count,"sending alert to %s of '%s'" % (get_connection(cnf.reporter.telephone_moh, reporter = get_reporter(cnf.reporter.national_id)), message)
                        if not self.dry:
                            self.send_message(get_connection(cnf.reporter.telephone_moh, reporter = get_reporter(cnf.reporter.national_id)), message)
                            cnf.sent = datetime.datetime.now()
                            cnf.responded = False
                            cnf.answer = False
                            cnf.save()
                    except Reporter.DoesNotExist:
                        pass
		
                elif cnf.reporter.role.code == 'binome':
                    try:
                        message_kw = 'Kuri Binome, Minisisteri y\'Ubuzima yakwemeje muri gahunda ya Rapidsms. Niba ubyemeye, subiza wohereza ijambo\
					  "Ndabyemeye" kuri 1110.'
                        if cnf.reporter.language == 'EN':
                            message = message_kw
                        elif cnf.reporter.language == 'FR':
                            message = message_kw

                        message = message_kw

                        print count,"sending alert to %s of '%s'" % (get_connection(cnf.reporter.telephone_moh, reporter = get_reporter(cnf.reporter.national_id)), message)
                        if not self.dry:
                            self.send_message(get_connection(cnf.reporter.telephone_moh, reporter = get_reporter(cnf.reporter.national_id)), message)
                            
                            cnf.sent = datetime.datetime.now()
                            cnf.responded = False
                            cnf.answer = False
                            cnf.save()
                    except Reporter.DoesNotExist:
                        pass

                if not self.dry:
                    try:	OutgoingMessage( text =  message,	identity = get_connection(cnf.reporter.telephone_moh, reporter = get_reporter(cnf.reporter.national_id)).identity ,	backend = get_connection(cnf.reporter.telephone_moh, reporter = get_reporter(cnf.reporter.national_id)).backend,	sent = datetime.datetime.now()).save()
    	    	    except:	pass

        except Reporter.DoesNotExist:
            pass

 
    def handle(self, **options):
        print "Running alerts to start.."

        self.dry = options['dry']

        if self.dry:
            self.dry = True
            print "DRY RUN -- No messages will be sent, no database commits made."

        # today
        today = datetime.date.today()
	self.check_alerts(to_sup = False)
