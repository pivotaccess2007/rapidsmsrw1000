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
    PREGNANCY REGISTRATION
    """

    keyword = "pre"
    
    def filter(self):
        if not getattr(msg, 'connection', None):
            self.respond(_("You need to be registered first, use the REG keyword"))
            return True 
    def help(self):
        self.respond("The correct format message is: PRE MOTHER_ID LAST_MENSES NEXT_VISIT PREVIOUS_RISK CURRENT_RISK LOCATION_CODE MOTHER_WEIGHT MOTHER_HEIGHT SANITATION TELEPHONE")

    def handle(self, text):
        #print self.msg.text
        return self.pregnancy(self.msg)
        self.respond(text)

    def pregnancy(self, message):
        """Incoming pregnancy reports.  This registers a new mother as having an upcoming child"""

        try: activate(message.contact.language)
        except:    activate('rw')

        #self.debug("PRE message: %s" % message.text)
        #print message, message.connection.identity
        try:
            message.reporter = message_reporter(message)#Reporter.objects.filter(national_id = message.connection.contact.name )[0]
        except Exception, e:
            message.respond(_("You need to be registered first, use the REG keyword"))
            return True
                    
        m = re.search("pre\s+(\d+)\s+([0-9.]+)\s([0-9.]+)\s([0-9]+)\s([0-9]+)\s?(.*)\s(hp|cl)\s(wt\d+\.?\d)\s(ht\d+\.?\d)\s(to|nt)\s(hw|nh)\s?(.*)",\
			 message.text, re.IGNORECASE)
        if not m:
            message.respond(_("The correct format message is: PRE MOTHER_ID LAST_MENSES NEXT_VISIT PREVIOUS_RISK CURRENT_RISK LOCATION_CODE MOTHER_WEIGHT MOTHER_HEIGHT SANITATION TELEPHONE"))
            return True
        
        try:    nid = read_nid(message, m.group(1))
        except Exception, e:
            # there were invalid fields, respond and exit
            message.respond("%s" % e)
            return True
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
        

        if gravity <= parity:
            message.respond(_("Parity cannot be greater or equal to Gravidity."))
            return True

        if ibibazo.lower().find('rm') >= 0 and int(gravity) == int(parity)+1:
            message.respond(_("Gravidity and Parity numbers are showing zero miscarriages."))
            return True 
        
        try:
            last_menses = parse_dob(lmp)
        except Exception, e:
            # date was invalid, respond
            message.respond("%s" % e)
            return True
            
    	#print message, message.connection, last_menses
        # get or create the patient
        patient = get_or_create_patient(message.reporter, nid)
        
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
            ##Remember for Pregnancy to adjust next appointment if given while scheduling the mother as follow
            report.set_preg_edd_dates(report.date)
            if next_visit:
                next_visit = datetime.strptime(parse_date(next_visit), "%d.%m.%Y").date()
                report.edd_anc2_date = next_visit            
                
            report.save()
            
        else:
    		message.respond(_("This report has been recorded, and we cannot duplicate it again. Thank you!"))
    		return True
        
        # then associate all our fields with it
        fields.append(read_weight(weight, weight_is_mothers=True))
        fields.append(read_height(height, height_is_mothers=True))
        fields.append(read_gravity(gravity))
        fields.append(read_parity(parity))
        fields.append(read_key(toilet))
        fields.append(read_key(handwash))
        fields.append(read_key(location))

        for field in fields:
            if field:
                field.report = report
                field.save()
                report.fields.add(field)
        bmi = read_bmi(report)
        report.bmi_anc1 = bmi
        report.save()

        if is_mother_weight_loss(report):
            forward(message, message.connection.identity, "Uyu mubyeyi %s yatakaje ibiro, nukureba uko wamugira inama." % report.patient.national_id)
     
        #print message, message.connection, last_menses, fields, patient,report
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
