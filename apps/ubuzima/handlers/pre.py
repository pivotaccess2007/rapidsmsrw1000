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


class PreHandler (KeywordHandler):
    """
    Handle any message prefixed ``echo``, responding with the remainder
    of the text. Useful for remotely testing internationalization.
    """

    keyword = "pre"
    
    def filter(self):
        if not getattr(message, 'connection', None):
            self.respond(_("You need to be registered first, use the REG keyword"))
            return True 
    def help(self):
        self.respond("To echo some text, send: ECHO <ANYTHING>")

    def handle(self, text):
        #print self.msg.text
        return self.pregnancy(self.msg)
        self.respond(text)

    def pregnancy(self, message):
        """Incoming pregnancy reports.  This registers a new mother as having an upcoming child"""

        #self.debug("PRE message: %s" % message.text)
        print message, message.connection
        
        m = re.search("pre\s+(\d+)\s+([0-9.]+)\s([0-9.]+)\s([0-9]+)\s([0-9]+)\s?(.*)\s(hp|cl)\s(wt\d+\.?\d)\s(ht\d+\.?\d)\s(to|nt)\s(hw|nh)\s?(.*)",\
			 message.text, re.IGNORECASE)
        if not m:
            message.respond(_("The correct format message is: PRE MOTHER_ID LAST_MENSES NEXT_VISIT PREVIOUS_RISK CURRENT_RISK LOCATION_CODE MOTHER_WEIGHT MOTHER_HEIGHT SANITATION TELEPHONE"))
            return True
        
        nid = m.group(1)
        lmp = m.group(2)
        next_visit = m.group(3)
        gravity = m.group(4)
        parity = m.group(5)
        ibibazo = m.group(6)
        location = m.group(7)
        weight = m.group(8)
        height = m.group(9)
        toilet = m.group(10)
        handwash = m.group(11)
        telephone = m.group(12)
        
        try:
            last_menses = parse_dob(lmp)
        except Exception, e:
            # date was invalid, respond
            message.respond("%s" % e)
            return True
            
    	#print message, message.connection, last_menses
        # get or create the patient
        patient = get_or_create_patient(message.connection.identity, nid)
        
        # create our report
        report = create_report('Pregnancy', patient, message.reporter)

        report.set_date_string(last_menses)
        
        # read our fields
        try:
            (fields, dob) = read_fields(ibibazo, False, False)
        except Exception, e:
            # there were invalid fields, respond and exit
            message.respond("%s" % e)
            return True
        
        # save the report
        print message, message.connection, last_menses, fields, patient
    	if not report.has_dups():
		report.save()
		    		
		try:

    			pregnancy = Pregnancy(report = report, plmp = datetime.strptime(parse_dob(lmp), "%d.%m.%Y").date(), \
						pnext_visit = datetime.strptime(parse_date(next_visit), "%d.%m.%Y").date(), mtelephone = "+25%s"%telephone)
    			pregnancy.save()
		except Exception, e:
			report.delete()	
			message.respond(_("Unknown Error, please check message format and try again."))	
        else:
    		message.respond(_("This report has been recorded, and we cannot duplicate it again. Thank you!"))
    		return True
        # then associate all our fields with it
        fields.append(read_weight(weight, weight_is_mothers=True))
        fields.append(read_height(height, height_is_mothers=True))
        fields.append(read_key(toilet))
        fields.append(read_key(handwash))
        fields.append(read_key(location))
        for field in fields:
            if field:
    	    	field.save()
            	report.fields.add(field)            

        # either return an advice text, or our default text for this message type
        try:	response = run_triggers(message, report)
        except:	response = None
        if response:
            message.respond(response)
        else:
            message.respond(_("Thank you! Pregnancy report submitted successfully."))
            
        # cc the supervisor if there is one
        try:	cc_supervisor(message, report)
        except:	pass  
  
        
        return True
