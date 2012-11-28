from django.db import models
from django.contrib.auth.models import *
from apps.logger.models import IncomingMessage
from apps.reporters.models import Reporter
from apps.ubuzima.models import Report, Field, Patient
from apps.locations.models import Location
from django.utils.translation import ugettext as _
import datetime
from decimal import Decimal

# Create your Django models here, if you need them.

class Child(models.Model):
    name = models.CharField(max_length=100, null = True)
    birth = models.ForeignKey(Report)
    dob = models.DateField(null=True)
    number = models.IntegerField()
    mother = models.ForeignKey(Patient)
    sex = models.CharField(max_length=1)
    born_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    muac = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    weight_6 = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    weight_9 = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    weight_18 = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    weight_24 = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    height_6 = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    height_9 = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    height_18 = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    height_24 = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    village = models.CharField(max_length=255, null=True)
    cell = models.ForeignKey(Location, related_name = 'childcell', null=True)
    sector = models.ForeignKey(Location, related_name = 'childsector', null=True)
    district = models.ForeignKey(Location, related_name = 'childdistrict', null=True)
    province = models.ForeignKey(Location, related_name = 'childprovince', null=True)
    nation = models.ForeignKey(Location, related_name = 'childnation', null=True)
	
    class Meta:
        verbose_name = "Connection"
        unique_together = ("number", "mother")

   # def is_underweight(self, weight, age):
    #    wfa = (weight/age)
        #return wfa
   # def is_stunted(self, height, age):
   #     stunt = (height/age)
    #    return stunted
    #def is_wasted(self, height, weight):
     #   waste = (height/weight)
      #  return waste

   # def save(self):
    #    self.total_cost = self.calc_total()
     #   super(Item, self).save() 

class ChildRisk(models.Model):
	child = models.ForeignKey(Child)
	risk = models.ForeignKey(Field)
