#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsmsrw1000.apps.ubuzima.models import *
from rapidsmsrw1000.apps.ambulances.models import *
from rapidsmsrw1000.apps.locations.models import *
from rapidsmsrw1000.apps.ubuzima.models import *
from rapidsmsrw1000.apps.reporters.models import *

from django.utils.translation import ugettext as _
from django.utils.translation import activate, get_language
from decimal import *
from exceptions import Exception
import traceback
from datetime import *
from time import *
from django.db.models import Q
from rapidsmsrw1000.apps.chws import models as confirm


def read_weight(code_string, weight_is_mothers=False):
	try:
	    field_type = FieldType.objects.get(key="child_weight" if not weight_is_mothers else "mother_weight")
	    value = Decimal(code_string[2:])
	    field = Field(type=field_type, value=value)
	    return field
	except:	return None

def read_height(code_string, height_is_mothers=False):
	try:
	    field_type = FieldType.objects.get(key="mother_height" if not height_is_mothers else "mother_height")
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
	    if len(dd) > 2 or len(mm) > 2 or len(yyyy) > 4: 
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
        
        patient = Patient.objects.create(national_id=national_id, location = reporter.location)

    return patient

def create_report(report_type_name, patient, reporter):
	"""Convenience for creating a new Report object from a reporter, patient and type """

	report_type = ReportType.objects.get(name=report_type_name)
	report = Report(patient=patient, reporter=reporter, type=report_type,
		        location=reporter.location, village=reporter.village)
	return report
    
def run_triggers(message, report):
	"""Called whenever we get a new report.  We run our triggers, figuring out if there 
	   are messages to send out to supervisors.  We return the message that should be sent
	   to the reporter themselves, or None if there is no matching trigger for the reporter."""
	# find all matching triggers
	triggers = TriggeredText.get_triggers_for_report(report)

	# the message we'll send back to the reporter
	reporter_message = None

	# for each one
	for trigger in triggers:
	    lang = get_language()
	    alert=TriggeredAlert(reporter=report.reporter, report=report, trigger=trigger)
	    alert.save()
	    curloc = report.location
	    if trigger.destination == TriggeredText.DESTINATION_AMB:
		while curloc:
		    ambs = AmbulanceDriver.objects.filter(location = curloc)
		    if len(ambs) < 1:
		        curloc = curloc.parent
		        continue
		    for amb in ambs: amb.send_notification(message, report)
		    break

	    # if the destination is the supervisor
	    elif trigger.destination != TriggeredText.DESTINATION_CHW:
		reporter_ident = report.reporter.connection().identity
		sup_group = ReporterGroup.objects.get(title='Supervisor')

		# figure out what location we'll use to find supervisors
		location = report.reporter.location

		# if we are supposed to tell the district supervisor and our current location 
		# is a health clinic, then walk up the tree looking for a hospital
		if trigger.destination == TriggeredText.DESTINATION_DIS and location.type.pk == 5:  # health center
		    # find the parent
		    if location.parent:
		        location = location.parent
		    # couldn't find it?  oh well, we'll alert the normal supervisor
		    
		# now look up to see if we have any reporters in this group 
		# with the same location as  our reporter
		sups = Reporter.objects.filter(groups=sup_group, location=location).order_by("pk")

		# for each supervisor
		for sup in sups:
		    # load the connection for it
		    conn = sup.connection()
		    lang = sup.language

		    # get th appropriate message to send
		    text = trigger.message_kw
		    if lang == 'en':
		        text = trigger.message_en
		    elif lang == 'fr':
		        text = trigger.message_fr
		
		    # and send this message to them
		    forward = _("%(phone)s: %(text)s" % { 'phone': reporter_ident, 'text': text })

		    message.forward(conn.identity, forward)

	    # otherwise, this is just a response to the reporter
	    else:
		# calculate our message based on language, we'll return it in a bit
		lang = get_language()
		reporter_message = trigger.message_kw
		if lang == 'en':
		    reporter_message = trigger.message_en
		elif lang == 'fr':
		    reporter_message = trigger.message_fr
	# return our advice texts
	return reporter_message
    
def cc_supervisor(message, report):
	""" CC's the supervisor of the clinic for this CHW   """

	# look up our supervisor group type
	sup_group = ReporterGroup.objects.get(title='Supervisor')

	# now look up to see if we have any reporters in this group with the same location as 
	# our reporter
	sups = Reporter.objects.filter(groups=sup_group, location=message.reporter.location).order_by("pk")

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
		forward = _("%(phone)s: %(report)s" % { 'phone': reporter_ident, 'report': report.as_verbose_string() })
		message.forward(conn.identity, forward)


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
	    if len(dd) > 2 or len(mm) > 2 or len(yyyy) > 4: 
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

