#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.db import models
from rapidsmsrw1000.apps.ubuzima.models import *
# Create your Django models here, if you need them.

class Pregnancy(models.Model):
    report = models.ForeignKey(Report)
    gravity = models.IntegerField(null=True)
    parity = models.IntegerField(null=True)
    plmp = models.DateField(null=True)
    pnext_visit = models.DateField(null=True)
    mtelephone  = models.CharField(max_length=13, null=True)


##save as
##pregnancy = Pregnancy(report = report, plmp = datetime.strptime(self.parse_dob(lmp), "%d.%m.%Y").date(), pnext_visit = datetime.strptime(self.parse_date(next_visit), "%d.%m.%Y").date(), mtelephone = "+25%s"%telephone)

    def __unicode__(self):
        return "Report: %s" % (self.report)




    
