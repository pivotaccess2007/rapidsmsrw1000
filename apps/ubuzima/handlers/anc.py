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


class AncHandler (KeywordHandler):
    """
    Handle any message prefixed ``echo``, responding with the remainder
    of the text. Useful for remotely testing internationalization.
    """

    keyword = "anc"

    def filter(self):
        if not getattr(message, 'connection', None):
            self.respond(_("You need to be registered first, use the REG keyword"))
            return True 
    def help(self):
        self.respond("To echo some text, send: ECHO <ANYTHING>")

    def handle(self, text):
        #print self.msg.text
        return self.anc(self.msg)
        self.respond(text)

    def anc(self, message):
	    """New Anc report. This is for regestering a new anc visit ."""
	
	    m = re.search("anc\s+(\d+)\s?(.*)", message.text, re.IGNORECASE)
	    if not m:
	        message.respond(_("The correct format message is: ANC MOTHER_ID ..."))
	        return True
	    received_patient_id = m.group(1)
	    optional_part=m.group(2)
	    anc_report=re.match("([0-9.]+)\s+(.*(\s*(anc2|anc3|anc4)\s*).*(\d+\.?\d*)(k|kg|kilo|kilogram).*)",optional_part,re.IGNORECASE)
	    anc_dep=re.match("(dp)\s?(.*)",optional_part,re.IGNORECASE)
	    last_visit=date.today()
	    if anc_report:
		    try:
		        last_visit = parse_dob(anc_report.group(1))
		    except Exception, e:
		        # date was invalid, respond
		        message.respond("%s" % e)
		        return True

	
	    if anc_dep:
		    pass		
	    if not anc_report and not anc_dep:
		    message.respond(_("The correct format message is: ANC MOTHER_ID LAST_VISIT ANC_ROUND ACTION_CODE MOTHER_WEIGHT"))
		    return True

	    if anc_report or anc_dep:
	        	# get or create the patient
		    patient = get_or_create_patient(message.reporter, received_patient_id)

		    # create our report
		    report = create_report('ANC', patient, message.reporter)
	    #date of last visit
	    if anc_report:
		    report.set_date_string(last_visit)
	        	# read our fields
	    try:
	        (fields, dob) = read_fields(optional_part,False, True)
	    except Exception, e:
	        # there were invalid fields, respond and exit
	        message.respond("%s" % e)
	        return True

	    # save the report
	    if not report.has_dups():
		    report.save()
	    else:
		    message.respond(_("This report has been recorded, and we cannot duplicate it again. Thank you!"))
		    return True

	    # then associate all the action codes with it
	    for field in fields:
	        field.save()
	        report.fields.add(field)            

	    # either send back the advice text or our default msg
	    if not Report.objects.filter(patient=patient,type__name='Pregnancy',created__gte=(date.today()-timedelta(270))):
		    message.respond("Thank you! ANC report submitted. Please send also the pregnancy report of this patient (%s)."%str(patient))
		    return True
	    response = run_triggers(message, report)
	    if response:
	        message.respond(response)
	    else:
	        message.respond(_("Thank you! ANC report submitted successfully."))
	        
	    # cc the supervisor if there is one
	    cc_supervisor(message, report)
	    return True 

	    #   TODO:
	    #   Muck with the translations.
