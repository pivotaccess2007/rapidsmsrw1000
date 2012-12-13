#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.db import models
from django.contrib.auth.models import *
from rapidsmsrw1000.apps.reporters.models import Reporter as OldRef
# Create your Django models here, if you need them.


class Role(models.Model):
	"""Basic representation of a role that someone can have.  For example,
		'supervisor' or 'data entry clerk'"""
	name = models.CharField(max_length=160, unique = True)
	code = models.CharField(max_length=20, unique = True, blank=True, null=True,\
	help_text="Abbreviation")

	def __unicode__(self):
		return self.name

class Nation(models.Model):
	"""Country....the maximum code is ten because of the last low level of ISO is village which usually has ten characters"""
	name = models.CharField(max_length=160)
	code = models.CharField(max_length=10, unique = True, blank=True, null=True,\
        			help_text="Country Own code in ISO Coding SYSTEM.....For Rwanda the code is 00. because the province are 01, 02, 03, 04, then 05")
    
	def __unicode__(self):
        	return self.name

class Province(models.Model):
	"""Province....the maximum code is ten because of the last low level of ISO is village which usually has ten characters"""
	name 	= models.CharField(max_length=160)
	code 	= models.CharField(max_length=10, unique = True,  blank=True, null=True,\
        				help_text="Province Own code in ISO Coding SYSTEM....")
	nation 	= models.ForeignKey(Nation, related_name="province_nation", null=True, blank=True, help_text=" The country the province is from") 
    
	def __unicode__(self):
        	return self.name

class District(models.Model):
	"""District....the maximum code is ten because of the last low level of ISO is village which usually has ten characters"""
	name 	 = models.CharField(max_length=160)
	code 	 = models.CharField(max_length=10, unique = True,  blank=True, null=True,\
        				help_text="District Own code in  ISO Coding SYSTEM .....")
	nation 	 = models.ForeignKey(Nation, related_name="district_nation", null=True, blank=True, help_text=" The country the district is from") 
	province = models.ForeignKey(Province, related_name="ditrict_province", null=True, blank=True, help_text=" The province the district is from")

	def __unicode__(self):
        	return self.name

class Sector(models.Model):
	"""Sector....the maximum code is ten because of the last low level of ISO is village which usually has ten characters"""
	name 	 = models.CharField(max_length=160)
	code 	 = models.CharField(max_length=10, unique = True,  blank=True, null=True,\
        				help_text="Sector Own code in  ISO Coding SYSTEM .....")
	nation 	 = models.ForeignKey(Nation, related_name="sector_nation", null=True, blank=True, help_text=" The country the sector is from") 
	province = models.ForeignKey(Province, related_name="sector_province", null=True, blank=True, help_text=" The province the sector is from")
	district		= models.ForeignKey(District, related_name="sector_district", null=True, blank=True, help_text=" The district the sector is from")
	
	def __unicode__(self):
        	return self.name

class Cell(models.Model):
	"""Cell....the maximum code is ten because of the last low level of ISO is village which usually has ten characters"""
	name 	 = models.CharField(max_length=160)
	code 	 = models.CharField(max_length=10, unique = True,  blank=True, null=True,\
        				help_text="Cell Own code in  ISO Coding SYSTEM .....")
	nation 	 = models.ForeignKey(Nation, related_name="cell_nation", null=True, blank=True, help_text=" The country the cell is from") 
	province = models.ForeignKey(Province, related_name="cell_province", null=True, blank=True, help_text=" The province the cell is from")
	district		= models.ForeignKey(District, related_name="cell_district", null=True, blank=True, help_text=" The cell the cell is from")
	sector			= models.ForeignKey(Sector, related_name="cell_sector", null=True, blank=True, help_text=" The sector the cell is from")

	def __unicode__(self):
        	return self.name

class Village(models.Model):
	"""Village....the maximum code is ten because of the last low level of ISO is village which usually has ten characters"""
	name 	 = models.CharField(max_length=160)
	code 	 = models.CharField(max_length=10, unique = True,  blank=True, null=True,\
        				help_text="Village Own code in  ISO Coding SYSTEM .....")
	nation 	 = models.ForeignKey(Nation, related_name="village_nation", null=True, blank=True, help_text=" The country the village is from") 
	province = models.ForeignKey(Province, related_name="village_province", null=True, blank=True, help_text=" The province the village is from")
	district		= models.ForeignKey(District, related_name="village_district", null=True, blank=True, help_text=" The cell the village is from")
	sector			= models.ForeignKey(Sector, related_name="village_sector", null=True, blank=True, help_text=" The sector the village is from")
	cell			= models.ForeignKey(Cell, related_name="village_cell", null=True, blank=True, help_text=" The cell the village is from")

	def __unicode__(self):
        	return self.name




class Hospital(models.Model):
	"""Hospital....the maximum code is ten because of the last low level of ISO is village which usually has ten characters"""
	name 	 = models.CharField(max_length=160)
	code 	 = models.CharField(max_length=10, unique = True,  blank=True, null=True,\
        				help_text="Hospital Own code in  FOSA Coding SYSTEM .....")
	nation 	 = models.ForeignKey(Nation, related_name="hospital_nation", null=True, blank=True, help_text=" The country the hospital is from") 
	province = models.ForeignKey(Province, related_name="hospital_province", null=True, blank=True, help_text=" The province the hospital is from")
	district		= models.ForeignKey(District, related_name="hospital_district", null=True, blank=True, help_text=" The district the hospital is from")
	sector			= models.ForeignKey(Sector, related_name="hospital_sector", null=True, blank=True, help_text=" The sector the hospital is from")
	def __unicode__(self):
        	return self.name

class HealthCentre(models.Model):
	"""Health Centre....the maximum code is ten because of the last low level of ISO is village which usually has ten characters"""
	name 	 = models.CharField(max_length=160)
	code 	 = models.CharField(max_length=10, unique = True,  blank=True, null=True,\
        				help_text="Health Centre Own code in  FOSA Coding SYSTEM .....")
	nation 	 = models.ForeignKey(Nation, related_name="hc_nation", null=True, blank=True, help_text=" The country the health centre is from") 
	province = models.ForeignKey(Province, related_name="hc_province", null=True, blank=True, help_text=" The province the health centre is from")
	district		= models.ForeignKey(District, related_name="hc_district", null=True, blank=True, help_text=" The district the health centre is from")
	sector			= models.ForeignKey(Sector, related_name="hc_sector", null=True, blank=True, help_text=" The sector the health centre is from")

	def __unicode__(self):
        	return self.name
	


class Reporter(models.Model):
	"""This model represents a KNOWN person, that can be identified via
		their alias and/or connection(s). Unlike the RapidSMS Person class,
		it should not be used to represent unknown reporters, since that
		could lead to multiple objects for the same "person". Usually, this
		model should be created through the WebUI, in advance of the reporter
		using the system - but there are always exceptions to these rules..."""

	education_primaire 	= 'P'
	education_secondaire 	= 'S'
	education_universite	= 'U'
	education_ntayo 	= 'N'
	sex_female		= 'F'
	sex_male		= 'M'
	language_english	= 'EN'
	language_french		= 'FR'
	language_kinyarwanda	= 'RW'
	

	SEX_CHOICES		= ( (sex_female, "Female"),
		            		(sex_male, "Male"))

	LANGUAGE_CHOICES = ( (language_english, "English"),
		            (language_french, "French"),
		            (language_kinyarwanda, "Kinyarwanda"))


	EDUCATION_CHOICES = ( (education_primaire, "Primary"),
		            (education_secondaire, "Secondary"),
		            (education_universite, "University"),
		            (education_ntayo, "None"))

	surname         	= models.CharField(max_length=50, blank=True, null = True, help_text="Family name please")
	given_name      	= models.CharField(max_length=50, blank=True, null = True, help_text="Other names")
	role            	= models.ForeignKey(Role, related_name="role", null=True, blank=True, help_text="The role you play in the community")
	sex 	        	= models.CharField(max_length = 1, blank=True, null = True, choices= SEX_CHOICES, help_text="Select the gender or sex")
	education_level 	= models.CharField(max_length = 1, blank=True, null = True, choices= EDUCATION_CHOICES, help_text="Select Education Level")
	date_of_birth		= models.DateField(blank=True, null = True, help_text="Your Date Of Birth, if date not known just pick First January")
	join_date		= models.DateField(blank=True, null = True, help_text="The date you joined the Community Health Worker program")
	national_id		= models.CharField(max_length=16, unique = True, help_text="The National ID as a sixteen digit please")
	telephone_moh		= models.CharField(max_length=13, unique = True, help_text="The telephone number only the one provided by Ministry of Health")
	village			= models.ForeignKey(Village, related_name="chw_village", null=True, blank=True, help_text=" The village you live in")
	cell			= models.ForeignKey(Cell, related_name="chw_cell", null=True, blank=True, help_text=" The cell you live in")
	sector			= models.ForeignKey(Sector, related_name="chw_sector", null=True, blank=True, help_text=" The sector you live in")
	health_centre		= models.ForeignKey(HealthCentre, related_name="chw_hc", null=True, blank=True, help_text=" The health centre you report to ")
	referral_hospital	= models.ForeignKey(Hospital, related_name="chw_hospital", null=True, blank=True, 
										help_text=" The referral hospital of the health centre you report to")
	district		= models.ForeignKey(District, related_name="chw_district", null=True, blank=True, help_text=" The district you live in")
	province		= models.ForeignKey(Province, related_name="chw_province", null=True, blank=True, help_text=" The province you live in")
	nation			= models.ForeignKey(Nation, related_name="chw_nation", null=True, blank=True, help_text=" The country you live in")
	created			= models.DateTimeField(auto_now_add = True, blank=True, null = True, help_text="The date you are registered in the RapidSMS System")
	updated			= models.DateTimeField(blank=True, null = True, help_text="The date of last modification about the current details of CHW")
	# the language that this reporter prefers to
	# receive their messages in, as a w3c language tag
	#
	# the spec:   http://www.w3.org/International/articles/language-tags/Overview.en.php
	# reference:  http://www.iana.org/assignments/language-subtag-registry
	#
	# to summarize:
	#   english  	= en
	#   french  	= fr
	#   kinyatwanda = rw
	#
	language = models.CharField(max_length = 2, blank=True, null = True, choices= LANGUAGE_CHOICES, help_text="Select the preferred language to receive SMS")
	deactivated = models.BooleanField(default=False, help_text="Deactivate Reporter Telephone Number when is no longer used.")
	old_ref = models.ForeignKey(OldRef, related_name="chw_old_ref", null=True, blank=True, help_text=" Old Reference in Rapidsms")

	def __unicode__(self):

		return self.telephone_moh


class RegistrationConfirmation(models.Model):
	"""This allow from those CHW we registered who have confirmed that are CHWs and who are not.
			Two days after we need to clone a reminder to ask registered CHWs to respond if they have not yet.
			We also need to print out a list of CHWs who have not responded after five days."""
	reporter  = models.ForeignKey(Reporter, related_name="chw", unique = True, help_text=" The reporter we sent a registration confirmation")
	sent	  = models.DateField(blank=True, null = True, help_text="The date RapidSMS sent the registration request")
	received  = models.DateField(blank=True, null = True, help_text="The date RapidSMS received the registration response from the CHWs")
	responded = models.BooleanField(default=False, help_text="Did the CHW responded?")
	answer	  = models.BooleanField(default=False, help_text="The answer from CHW")

	def __unicode__(self):
		return "%s : %s" % (self.reporter.telephone_moh, self.answer)

def fosa_to_code(fosa_id):
    """Given a fosa id, returns a location code"""
    return "F" + fosa_id

def code_to_fosa(code):
    """Given a location code, returns the fosa id"""
    return code[1:]

class Error(models.Model):
	row = models.CharField(max_length = 10)
	sheet = models.CharField(max_length = 50)
	upload_ref = models.CharField(max_length = 50)
	district = models.ForeignKey(District)
	when	 = models.DateTimeField()	
        by	 = models.ForeignKey(User)
	error_message = models.CharField(max_length = 300)

	def __unicode__(self):
		return self.row

class Warn(models.Model):
	row = models.CharField(max_length = 10)
	sheet = models.CharField(max_length = 50)
	upload_ref = models.CharField(max_length = 50)
	district = models.ForeignKey(District)
	when	 = models.DateTimeField()	
        by	 = models.ForeignKey(User)
	warning_message = models.CharField(max_length = 300)

	def __unicode__(self):
		return self.row


class Supervisor(models.Model):
    names = models.EmailField(max_length=150, null=True)
    dob = models.DateField(blank=True, null = True, help_text="Date Of Birth")
    area_level = models.CharField(max_length=13, null=True)
    village = models.ForeignKey(Village, null = True)
    cell = models.ForeignKey(Cell, null = True)
    sector = models.ForeignKey(Sector, null = True)
    health_centre = models.ForeignKey(HealthCentre, null = True)
    hospital = models.ForeignKey(Hospital, null = True)
    district = models.ForeignKey(District, null = True)
    province = models.ForeignKey(Province, null = True)
    nation = models.ForeignKey(Nation, null = True)
    telephone  = models.CharField(max_length=13, null=True, unique = True)
    email = models.EmailField(max_length=50, null=True)
    random_nid =  models.CharField(max_length=16, null=True, unique = True)

    def __unicode__(self):
        return "Supervisor: %s" % (self.names)

    
