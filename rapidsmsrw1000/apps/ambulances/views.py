#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import csv
from datetime import date, timedelta
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseServerError, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404
from django.db import transaction, connection
from django.db.models import Q

from sys import getdefaultencoding
from rapidsmsrw1000.apps.ambulances.models import *


def alphabets(current = None):
    locs = []
    for x in HealthCentre.objects.all(): locs.append(x)
    for x in Hospital.objects.all(): locs.append(x)
    for x in District.objects.all(): locs.append(x)
    ans = list(set([x.name[0].upper() for x in locs]))
    ans.sort()
    return ans

@permission_required('ambulances.can_view')
def ambulances_by_alphabet(req, letter):
    req.base_template = "webapp/layout.html"
    locations = []
    for x in HealthCentre.objects.filter( name__startswith = letter.upper()): locations.append(x)
    for x in Hospital.objects.filter( name__startswith = letter.upper()): locations.append(x)
    for x in District.objects.filter( name__startswith = letter.upper()): locations.append(x)
    ##Need to sort ibitaro n'uturere in locations 
    locations.sort(key = lambda x: x.name)
    return render_to_response('ambulances/ambulances.html',
            {'locations': locations, 'alphabets': alphabets(letter), 'letter':letter}, context_instance=RequestContext(req))

@permission_required('ambulances.can_view')
def ambulances(req):
    req.base_template = "webapp/layout.html"
    #   locations = Location.objects.all().order_by('name')
    return render_to_response( 'ambulances/ambulances.html',
            {'locations': [], 'alphabets': alphabets(), 'letter':None},  context_instance=RequestContext(req))

@permission_required('ambulances.can_view')
def ambulances_by_location(req, loc):
    req.base_template = "webapp/layout.html"
    drivers = location = None
    try:
        location = HealthCentre.objects.get(code = loc)
        drivers  = AmbulanceDriver.objects.filter(health_centre = location).order_by('name')
    except HealthCentre.DoesNotExist, e:
        try:
            location = Hospital.objects.get(code = loc)
            drivers  = AmbulanceDriver.objects.filter(referral_hospital = location).order_by('name')
        except Hospital.DoesNotExist, e:
            try:
                location = District.objects.get(code = loc)
                drivers  = AmbulanceDriver.objects.filter(district = location).order_by('name')
            except District.DoesNotExist, e:
                pass
                
    return render_to_response( 'ambulances/ambulance_locations.html',
            {'location': location, 'drivers': drivers},  context_instance=RequestContext(req))

@permission_required('ambulances.can_view')
def ambulance_driver_add(req):
    req.base_template = "webapp/layout.html"
    loxn = driver = None
    try:
        loxn = HealthCentre.objects.get(code = req.POST['vers'])
        driver = AmbulanceDriver(phonenumber = req.POST['nimero'], name = req.POST['nom'], identity = req.POST['natid'],\
                                         health_centre = loxn, district = loxn.district)
    except HealthCentre.DoesNotExist, e:
        try:
            loxn = Hospital.objects.get(code = req.POST['vers'])
            driver = AmbulanceDriver(phonenumber = req.POST['nimero'], name = req.POST['nom'], identity = req.POST['natid'],\
                                         referral_hospital = loxn, district = loxn.district)
        except Hospital.DoesNotExist, e:
            try:
                loxn = District.objects.get(code = req.POST['vers'])
                driver = AmbulanceDriver(phonenumber = req.POST['nimero'], name = req.POST['nom'], identity = req.POST['natid'],\
                                         district = loxn)
            except District.DoesNotExist, e:
                pass
    driver.save()    
    return HttpResponseRedirect('/ambulances/location/%s' % (loxn.code,))

@permission_required('ambulances.can_view')
def ambulance_driver_delete(req):
    req.base_template = "webapp/layout.html"
    loxn = driver = None
    try:
        loxn = HealthCentre.objects.get(code = req.POST['vers'])
        driver = AmbulanceDriver.objects.get(health_centre__code = loxn.code ,id = int(req.POST['drv']))
    except HealthCentre.DoesNotExist, e:
        try:
            loxn = Hospital.objects.get(code = req.POST['vers'])
            driver = AmbulanceDriver.objects.get(referral_hospital__code = loxn.code ,id = int(req.POST['drv']))
        except Hospital.DoesNotExist, e:
            try:
                loxn = District.objects.get(code = req.POST['vers'])
                driver = AmbulanceDriver.objects.get(district__code = loxn.code ,id = int(req.POST['drv']))
            except District.DoesNotExist, e:
                pass
    
    driver.delete()
    return HttpResponseRedirect('/ambulances/location/%s' % (loxn.code,))

@permission_required('ambulances.can_view')
def ambulance_add(req):
    loxn      = Location.objects.get(id = int(req.POST['vers']))
    ambulance = Ambulance(plates = req.POST['nimero'], station = loxn)
    ambulance.save()
    return HttpResponseRedirect('/ambulances/location/%d' % (loxn.id,))
