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
    ANC REGISTRATION
    """

    keyword = "anc"
    
    def filter(self):
        if not getattr(msg, 'connection', None):
            self.respond(_("You need to be registered first, use the REG keyword"))
            return True 
    def help(self):
        self.respond("The correct format message is: ANC MOTHER_ID VISIT_DATE ANC_ROUND ACTION_CODE LOCATION_CODE MOTHER_WEIGHT")

    def handle(self, text):
        #print self.msg.text
        return self.anc(self.msg)
        self.respond(text)

    def anc(self, message):
    	"""New Anc report. This is for regestering a new anc visit ."""
        try: activate(message.contact.language)
        except:    activate('rw')
        
    	try:
            message.reporter = message_reporter(message)#Reporter.objects.filter(national_id = message.connection.contact.name )[0]
            
        except Exception, e:
            message.respond(_("You need to be registered first, use the REG keyword"))
            return True
        
        m = re.search("anc\s+(\d+)\s+([0-9.]+)\s(anc2|anc3|anc4)\s?(.*)\s(hp|cl)\s(wt\d+\.?\d*)\s?(.*)", message.text, re.IGNORECASE)
        if not m:
            message.respond(_("The correct format message is: ANC MOTHER_ID VISIT_DATE ANC_ROUND ACTION_CODE LOCATION_CODE MOTHER_WEIGHT"))
            return True
        
        try:    nid = read_nid(message, m.group(1))
        except Exception, e:
            # there were invalid fields, respond and exit
            message.respond("%s" % e)
            return True
        visit = m.group(2)
        tour = m.group(3)
        ibibazo = m.group(4)
        location = m.group(5)
        weight = m.group(6)
    	try:
    	    last_visit = parse_dob(visit)
    	except Exception, e:
	    # date was invalid, respond
	        message.respond("%s" % e)
	        return True
        # get or create the patient
        patient = get_or_create_patient(message.reporter, nid)

        # create our report
        report = create_report('ANC', patient, message.reporter)
        #date of last visit
        report.set_date_string(last_visit)

        # read our fields
        try:
            (fields, dob) = read_fields(ibibazo,False, True)
        except Exception, e:
            # there were invalid fields, respond and exit
            message.respond("%s" % e)
            return True

        # save the report
        for f in fields:
            if f.type in FieldType.objects.filter(category__name = 'Red Alert Codes'):
                message.respond(_("%(key)s:%(red)s is a red alert, please see how to report a red alert and try again.")\
                                         % { 'key': f.type.key,'red' : f.type.kw})
                return True

        for f in fields:
            if f.type in FieldType.objects.filter(category__name = 'Death Codes'):
                message.respond(_("%(key)s:%(dth)s is a death, please see how to report a death and try again.")\
                                         % { 'key': f.type.key,'dth' : f.type.kw})
                return True

        if not report.has_dups():
            	report.save()
        else:
	        message.respond(_("This report has been recorded, and we cannot duplicate it again. Thank you!"))
	        return True
        
        # then associate all our fields with it
        fields.append(read_weight(weight, weight_is_mothers=True))
        fields.append(read_key(tour))
        fields.append(read_key(location))
        
        for field in fields:
            if field:
                field.report = report
                field.save()
                report.fields.add(field)
        created = date.today()-timedelta(270)

        if not Report.objects.filter(patient=patient,type__name='Pregnancy',created__gte = date.today()-timedelta(270)):
            message.respond(_("Thank you! ANC report submitted. Please send also the pregnancy report of this patient %(nid)s.") % {'nid' : patient.national_id})
            return True

        # either send back the advice text or our default msg
        try:	response = run_triggers(message, report)
        except:	response = None
	                
        #   TODO:
        #   Muck with the translations.
        # cc the supervisor if there is one
        try:	cc_supervisor(message, report)
        except:	pass    	
        return True 

        #   TODO:
        #   Muck with the translations.
