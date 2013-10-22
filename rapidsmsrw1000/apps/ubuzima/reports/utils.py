#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsmsrw1000.apps.ubuzima.models import *
from rapidsmsrw1000.apps.ambulances.models import *
from rapidsmsrw1000.apps.ubuzima.models import *
from rapidsmsrw1000.apps.chws.models import *


from django.utils.translation import ugettext as _
from django.utils.translation import activate, get_language
from decimal import *
from exceptions import Exception
import traceback
from datetime import *
from time import *
from django.db.models import Q
from django.conf import settings
import re
from random import randint

from rapidsms.router import send
from rapidsms.models import Connection

def forward (message, identity, text):
    
    if message.connection:
        conn, created = Connection.objects.get_or_create(backend = message.connection.backend, identity = identity)        
        send( text, conn)
        #print conn, text     
        return True
    else:
        return False


def read_weight(code_string, weight_is_mothers=False):
	try:
	    field_type = FieldType.objects.get(key="child_weight" if not weight_is_mothers else "mother_weight")
	    value = Decimal(code_string[2:])
	    field = Field(type=field_type, value=value)
	    return field
	except:	return None

def read_height(code_string, height_is_mothers=False):
	try:
	    field_type = FieldType.objects.get(key="child_height" if not height_is_mothers else "mother_height")
	    value = Decimal(code_string[2:])
	    field = Field(type=field_type, value=value)
	    return field
	except:	return None

def read_key(code_string):
	try:
	    field_type = FieldType.objects.get(key = code_string.lower())
	    
	    field = Field(type=field_type)
	    return field
	except:	return None

def parse_date(dob_string):
	"""Tries to parse a string into some kind of date representation.  Note that we don't use Date objects
	   to store things away, because we want to accept limited precision dates, ie, just the year if 
	   necessary."""
	   
	# simple #### date.. ie, 1987 or 87
	m3 = re.search("^(\d+)$", dob_string)

	if m3:
	    value = m3.group(1)
	    
	    # two digit date, guess on the first digits based on size
	    if len(value) == 2:
		if int(value) <= date.today().year % 100:
		    value = "20%s" % value
		else:
		    value = "19%s" % value
			        
	    # we have a four digit date, does it look reasonable?
	    if len(value) == 4:
		return value
		    
	# full date: DD.MM.YYYY
	m3 = re.search("^(\d+)\.(\d+)\.(\d+)$", dob_string) 
	if m3:
	    dd = m3.group(1)
	    mm = m3.group(2)
	    yyyy = m3.group(3)
	    
	    # print "%s = '%s' '%s' '%s'" % (dob_string, dd, mm, yyyy)
	    
	    # make sure we are in the right format
	    if len(dd) > 2 or len(mm) > 2 or len(yyyy) != 4 or int(yyyy) < 2009: 
		raise Exception(_("Invalid date format, must be in the form: DD.MM.YYYY"))

	    # invalid month
	    if int(mm) > 12 or int(mm) < 1:
		raise Exception(_("Invalid date format, must be in the form: DD.MM.YYYY"))
	    
	    # invalid day
	    if int(dd) > 31 or int(dd) < 1:
		raise Exception(_("Invalid date format, must be in the form: DD.MM.YYYY"))
	    
	    
	    # Otherwise, parse into our format
	    return "%02d.%02d.%04d" % (int(dd), int(mm), int(yyyy))
	    
	return None

def read_fields(code_string, accept_date=False, weight_is_mothers=False):
	"""Tries to parse all the fields according to our set of action and movement codes.  We also 
	   try to figure out if certain fields are dates and stuff them in as well. """

	# split our code string by spaces
	codes = code_string.split()
	fields = []
	invalid_codes = []
	num_mov_codes = 0

	# the dob we might extract from this
	dob = None

	# for each code
	for code in codes:
	    try:
		# first try to look up the code in the DB
		field_type = FieldType.objects.get(key=code.lower())
		fields.append(Field(type=field_type))
		7
		# if the action code is a movement code, increment our counter of movement codes
		# messages may only have one movement code
		if field_type.category.id == 4:
		    num_mov_codes += 1

	    # didn't recognize this code?  then it is a scalar value, run some regexes to derive what it is
	    except FieldType.DoesNotExist:
		m1 = re.search("(\d+\.?\d*)(k|kg|kilo|kilogram)", code, re.IGNORECASE)
		m2 = re.search("(\d+\.?\d*)(c|cm|cent|centimeter)", code, re.IGNORECASE)
	
		# this is a weight
		if m1:
		    field_type = FieldType.objects.get(key="child_weight" if not weight_is_mothers else "mother_weight")
		    value = Decimal(m1.group(1))
		    field = Field(type=field_type, value=value)
		    fields.append(field)
		    
		# this is a length
		elif m2:
		    field_type = FieldType.objects.get(key="muac")
		    value = Decimal(m2.group(1))
		    field = Field(type=field_type, value=value)
		    fields.append(field)
		    
		# unknown
		else:
		    # try to parse as a dob
		    date = parse_dob(code)

		    if accept_date and date:
			dob = date
		    else:
			invalid_codes.append(code)

	# take care of any error messaging
	error_msg = ""
	if len(invalid_codes) > 0:
	    error_msg += _("Unknown action code: %(invalidcode)s.  ") % \
		{ 'invalidcode':  ", ".join(invalid_codes)}
	    
	if num_mov_codes > 1:
	    error_msg += unicode(_("You cannot give more than one location code"))

	if error_msg:
	    error_msg = _("Error.  %(error)s") % { 'error': error_msg }
	    
	    # there's actually an error, throw it over the fence
	    raise Exception(error_msg)

	return (fields, dob)

def get_or_create_patient(reporter, national_id):
    """Takes care of searching our DB for the passed in patient.  Equality is determined
	   using the national id only (IE, dob doesn't come into play).  This will create a 
	   new patient with the passed in reporter if necessary."""
    
    # try to look up the patent by id
    try:
        patient = Patient.objects.get(national_id=national_id)
    except Patient.DoesNotExist, e:
        # not found?  create the patient instead
        
        patient = Patient.objects.create(national_id=national_id, location = reporter.health_centre)

    return patient

def create_report(report_type_name, patient, reporter):
	"""Convenience for creating a new Report object from a reporter, patient and type """

	report_type = ReportType.objects.get(name=report_type_name)
	report = Report(patient=patient, reporter=reporter, type=report_type,
		        location=reporter.health_centre, village=reporter.village)
	return report
    
def run_triggers(message, report):
    """Called whenever we get a new report.  We run our triggers, figuring out if there 
	   are messages to send out to supervisors.  We return the message that should be sent
	   to the reporter themselves, or None if there is no matching trigger for the reporter."""
    try:
        # find all matching triggers
        triggers = TriggeredText.get_triggers_for_report(report)
        
        # the message we'll send back to the reporter
        reporter_message = None
         
        # for each one
        for trigger in triggers:
            
            lang = get_language()
            alert = TriggeredAlert(reporter=report.reporter, report=report, trigger=trigger, location = report.location, village = report.reporter.village,\
                                 cell = report.reporter.cell, sector = report.reporter.sector, district = report.reporter.district,\
                                 province = report.reporter.province, nation= report.reporter.nation)
            alert.save()
            curloc = report.location

            
            
            # if the destination is the reporter himself, need to respond correctly
            if trigger.destination == TriggeredText.DESTINATION_CHW:
                                        
                # calculate our message based on language, we'll return it in a bit
                lang = get_language()
                reporter_message = trigger.message_kw
                if lang == 'en':
                    reporter_message = trigger.message_en
                elif lang == 'fr':
                    reporter_message = trigger.message_fr
                
                 
            # if we are supposed to tell the district supervisor and our current location 
            # is a health clinic, then walk up the tree looking for a hospital

            elif trigger.destination == TriggeredText.DESTINATION_DIS or trigger.destination == TriggeredText.DESTINATION_SUP:
                # find the parent
                location = curloc
                sups = Supervisor.objects.filter(health_centre = location).order_by("pk")
                if trigger.destination == TriggeredText.DESTINATION_DIS:
                    cc_facilitystaff(message, report, trigger)
                # couldn't find it?  oh well, we'll alert the normal supervisor
		                    
                #print [sup.connection() for sup in sups]
                # for each supervisor
                for sup in sups:
                    # load the connection for it
                    conn = sup.connection()
                    lang = sup.language

                    # get th appropriate message to send
                    text = trigger.message_kw
                    code_lang = trigger.triggers.all()[0].kw
                    if lang == 'en':
                        text = trigger.message_en
                        code_lang = trigger.triggers.all()[0].en
                    elif lang == 'fr':
                        text = trigger.message_fr
                        code_lang = trigger.triggers.all()[0].fr

                    # and send this message to them
                    msg_forward = text % (message.connection.identity, report.patient.national_id, report.reporter.village, code_lang)

                    forward(message, conn.identity, msg_forward)            
            
            elif trigger.destination == TriggeredText.DESTINATION_AMB:
                           
                try:
                    ambs = AmbulanceDriver.objects.filter(health_centre = curloc)
                    
                    if ambs.count() < 1:
                        curloc = report.reporter.referral_hospital
                        ambs = AmbulanceDriver.objects.filter(referral_hospital = curloc)
                    
                    for amb in ambs:                    
                        amb.send_notification(message, report)
                        forward(message, amb.phonenumber, trigger.message_kw % (message.connection.identity, report.patient.national_id, report.reporter.village, trigger.triggers.all()[0].kw))                
                except Exception, e:
                    print e
                    continue

            
	    # return our advice texts
        if is_mother_weight_loss(report):
            forward(message, message.connection.identity, "Uyu mubyeyi %s yatakaje ibiro, nukureba uko wamugira inama." % report.patient.national_id)
        elif is_mother_risky(report):
            forward(message, message.connection.identity, "Uyu mubyeyi %s afite uburebure budashyitse, nukureba uko mwamuba hafi kugeza abyaye." \
                            % report.patient.national_id)
          
        return reporter_message
    except Exception, e:
        print e
        return None
    
def cc_supervisor(message, report):
    """ CC's the supervisor of the clinic for this CHW   """
    try:       
        
        # now look up to see if we have any reporters in this group with the same location as 
        # our reporter
        sups = Supervisor.objects.filter(health_centre = message.reporter.health_centre).order_by("pk")

        # reporter identity
        reporter_ident = message.reporter.connection().identity

        #reporter village
        reporter_village = message.reporter.village

        # we have at least one supervisor
        if sups:
            for sup in sups:
                # load the connection for it
                conn = sup.connection()

                # and send this message to them
                msg_forward = _("%(phone)s: %(report)s" % { 'phone': reporter_ident, 'report': report.as_verbose_string() })
                forward(message, conn.identity, msg_forward)
    except Exception, e:
        #print e
        pass

def cc_facilitystaff(message, report, trigger):
    """ CC's Facility Staff of the clinic for this CHW   """
    try:       

        fss = []
        
        for f in FacilityStaff.objects.filter(referral_hospital = report.reporter.referral_hospital):   fss.append(f)
        
        # for each facility staff
        for fs in fss:
            # load the connection for it
            
            try:    conn = fs.connection()
            except:
                try:
                    conn, created = Connection.objects.get_or_create(identity = fs.telephone_moh, backend = message.connection.backend)
                    conn.contact, created = Contact.objects.get_or_create(name = fs.national_id, language = 'rw')
                    conn.save()
                except: continue
                
            lang = fs.language

            # get th appropriate message to send
            text = trigger.message_kw
            code_lang = trigger.triggers.all()[0].kw
            if lang == 'en':
                text = trigger.message_en
                code_lang = trigger.triggers.all()[0].en
            elif lang == 'fr':
                text = trigger.message_fr
                code_lang = trigger.triggers.all()[0].fr
            
            msg_forward = text % (message.connection.identity, report.patient.national_id, report.reporter.village, code_lang)
            #print msg_forward, fs, conn
            if conn:    forward(message, conn.identity, msg_forward)
    except Exception, e:
        #print e
        pass


def parse_dob(dob_string):
	"""Tries to parse a string into some kind of date representation.  Note that we don't use Date objects
	   to store things away, because we want to accept limited precision dates, ie, just the year if 
	   necessary."""
	   
	# simple #### date.. ie, 1987 or 87
	m3 = re.search("^(\d+)$", dob_string)

	if m3:
	    value = m3.group(1)
	    
	    # two digit date, guess on the first digits based on size
	    if len(value) == 2:
		if int(value) <= date.today().year % 100:
		    value = "20%s" % value
		else:
		    value = "19%s" % value
		                
	    # we have a four digit date, does it look reasonable?
	    if len(value) == 4:
		return value
		    
	# full date: DD.MM.YYYY
	m3 = re.search("^(\d+)\.(\d+)\.(\d+)$", dob_string) 
	if m3:
	    dd = m3.group(1)
	    mm = m3.group(2)
	    yyyy = m3.group(3)
	    
	    # print "%s = '%s' '%s' '%s'" % (dob_string, dd, mm, yyyy)
	    
	    # make sure we are in the right format
	    if len(dd) > 2 or len(mm) > 2 or len(yyyy) != 4  or int(yyyy) < 2009: 
		raise Exception(_("Invalid date format, must be in the form: DD.MM.YYYY"))

	    # invalid month
	    if int(mm) > 12 or int(mm) < 1:
		raise Exception(_("Invalid date format, must be in the form: DD.MM.YYYY"))
	    
	    # invalid day
	    if int(dd) > 31 or int(dd) < 1:
		raise Exception(_("Invalid date format, must be in the form: DD.MM.YYYY"))
	    
	    # is the year in the future
	    if int(yyyy) > int(date.today().year):
		raise Exception(_("Invalid date, cannot be in the future."))
		    #is the the date in future
	    dob="%02d.%02d.%04d" % (int(dd), int(mm), int(yyyy))
	    if datetime.strptime(dob,"%d.%m.%Y").date() > date.today():
	    	raise Exception(_("Invalid date, cannot be in the future."))
	    
	    # Otherwise, parse into our format
	    return "%02d.%02d.%04d" % (int(dd), int(mm), int(yyyy))
	    
	return None

def read_muac(code_string):
    try:
        field_type = FieldType.objects.get(key="muac")
        value = Decimal(code_string[4:])
        field = Field(type=field_type, value=value)
        return field
    except:	return None

def read_number(code_string):
    try:
        field_type = FieldType.objects.get(key="child_number")
        value = Decimal(code_string)
        field = Field(type=field_type, value=value)
        return field
    except:	return None

def read_gravity(code_string):
    try:
        field_type = FieldType.objects.get(key="gravity")
        value = Decimal(code_string)
        field = Field(type=field_type, value=value)
        return field
    except:	return None
def read_parity(code_string):
    try:
        field_type = FieldType.objects.get(key="parity")
        value = Decimal(code_string)
        field = Field(type=field_type, value=value)
        return field
    except:	return None

def read_bmi(report):
    try:
        weight = report.fields.get(type__key = 'mother_weight').value
        height = report.fields.get(type__key = 'mother_height').value
        bmi = weight*100*100/(height*height)
        return bmi
    except:	pass

def is_mother_weight_loss(report):
    try:
        weight = report.fields.get(type__key = 'mother_weight').value
        history = Report.objects.filter(patient = report.patient).order_by('-id')[0].fields.get(type__key = 'mother_weight').value
        if weight < history:    return True
        else:   return False 
    except: return False

def is_mother_risky(report):
    try:
        height = report.fields.get(type__key = 'mother_height').value
        if height < 145:    return True
        else:   return False 
    except: return False


def read_nid(message, nid):
    if len(nid) != 16:
        err = ErrorNote(errmsg = message.text, type = ErrorType.objects.get(name = "Invalid ID"), errby = message.reporter, identity =\
		                message.connection.identity, location =message.reporter.health_centre , village=message.reporter.village,\
                        cell = message.reporter.cell, sector = message.reporter.sector, district = message.reporter.health_centre.district,\
                         province = message.reporter.health_centre.province, nation =   message.reporter.health_centre.nation).save()
        
        raise Exception(_("Error.  National ID must be exactly 16 digits, you sent the nid: %(nat_id)s with only %(uburefu)d digits") % 
                            { "nat_id": nid , "uburefu": len(nid) } )
        
        
        
        
    else:   return nid


def set_date_string(date_string):
    """
    Trap anybody setting the date_string and try to set the date from it.
    """
    try:
        date = datetime.strptime(date_string, "%d.%m.%Y").date()
    	return date    
    except ValueError,e:
        # no-op, just keep the date_string value
        pass

def message_reporter(message):
    try:
        return Reporter.objects.filter(national_id = message.connection.contact.name , deactivated = False)[0]
    except :
        if settings.TRAINING_ENV == True:   return anonymous_reporter(message.connection.identity)
        else:   raise Exception(_("You need to be registered first"))

def anonymous_reporter(identity):
    reporter = None
    try:
        names = "ANONYMOUS"
        telephone = identity
        
        try:
            hc = HealthCentre.objects.get(name = "TEST")
            hp = Hospital.objects.get(name = "TEST")
            telephone = parse_phone_number(telephone)
            nid = "%s%s" % ( telephone[3:] , str(random_with_N_digits(6)))
            try:    tester = Reporter.objects.get(telephone_moh = telephone, health_centre = hc, referral_hospital = hp)
            except:
                tester, created = Reporter.objects.get_or_create(telephone_moh = telephone, national_id = nid, health_centre = hc, referral_hospital = hp)

            tester.surname      = names	
            tester.role            = Role.objects.get(code = 'asm')	
            tester.sex 	        =  Reporter.sex_male	
            tester.education_level = Reporter.education_universite
            tester.date_of_birth   =	datetime.today()	
            tester.join_date		=   datetime.today()
            tester.district		=   hc.district
            tester.nation			=   hc.nation
            tester.province		=   hc.province
            tester.sector			=   Sector.objects.get(name = 'TEST')
            
            tester.cell			=	Cell.objects.get(name = 'TEST')
            tester.village		=   Village.objects.get(name = 'TEST')      
            tester.updated		    = datetime.now()
            tester.language        = Reporter.language_kinyarwanda
            
            tester.save()
            confirm, created = RegistrationConfirmation.objects.get_or_create(reporter = tester)
            confirm.save()
            reporter = tester    
        except Exception, e:
            print e
            pass
        
    except Exception, e:
        print e
        pass
    
    return reporter

def parse_phone_number(number):

    number = number
    try:
        number = str(int(float(number)))
    except:
        try:
            number = str(int(number))
        except:
            try:
                number = str(number)
            except:
                    return False
    number = number.replace(" ", "")
    try:
        if type(number)!=str:
            number=str(int(number))
        if number[:3]=="+25" and len(number[3:])==10:
            number=number
        elif number[:3]=="250" and len(number[3:])==9:
            number="+"+number
        elif number[:3]=="078" and len(number[3:])==7:
            number="+25"+number
        elif number[:2]=="78" and len(number[2:])==7:
            number="+250"+number
        return number
    except: 
            return False

def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

def valid_red_field(f, report):

    if f.type.key == 'np' or f.type.key == 'aa' or f.type.key == 'hp' or f.type.key == 'cl': return False
    
    elif report.type.name == 'Red Alert':
        if f.type.key == 'mw' or f.type.key == 'cw' or f.type.key == 'ms' or f.type.key == 'cs' : return False
                
    if report.type.name == 'Red Alert Result':
        if f.type.key == 'mw' and 'ms' in [j.type.key for j in report.fields.all()]: return False
        elif f.type.key == 'ms' and 'mw' in [j.type.key for j in report.fields.all()]: return False
        elif f.type.key == 'cw' and 'cs' in [j.type.key for j in report.fields.all()]: return False
        elif f.type.key == 'cs' and 'cw' in [j.type.key for j in report.fields.all()]: return False

    return True

def check_is_red(fields):
    cats = [f.type.category for f in fields]    
    if FieldCategory.objects.get(name = 'Red Alert Codes') in cats:
        return True    
    return False

def valid_ccm_or_cmr(fields, report):
    not_allowed_keys = ['np']
    keys = []
    for f in fields:
        if f.type.key in not_allowed_keys:
            return False
        else:
            keys.append(f.type.key)
    #print keys
    
    if 'ma' in keys or 'pc' in keys or 'di' in keys:
        return True
    
    return False        
