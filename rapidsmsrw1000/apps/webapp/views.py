#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.http import HttpResponse
#######
#from rapidsms.webui.utils import render_to_response
from django.template import RequestContext
from django.shortcuts import render_to_response
##############
from django.views.decorators.cache import cache_page
from django.contrib.auth.views import login as django_login
from django.contrib.auth.views import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt,csrf_protect
#from rapidsms.webui import settings
from rapidsmsrw1000.settings import *

def check_availability(req):
    return HttpResponse("OK")

def dashboard(req):
    return render_to_response("webapp/dashboard.html", context_instance=RequestContext(req))

def login(req, template_name="webapp/login.html"):
    '''Login to rapidsms'''
    
    req.base_template = "webapp/layout.html" 
    
    
    
    return django_login(req, **{"template_name" : template_name})

def logout(req, template_name="webapp/loggedout.html"):
    '''Logout of rapidsms'''
    req.base_template = "webapp/layout.html"
    return django_logout(req, **{"template_name" : template_name})

def working_area(req):
    
    return render_to_response("webapp/layout.html",context_instance=RequestContext(req))

def matching_report(req, diced, alllocs = False):
    rez = {}
    pst = {}
    try:
        rez['created__gte'] = diced['period']['start']
        rez['created__lte'] = diced['period']['end']+timedelta(1)
    except KeyError:
        pass
    return rez

@csrf_exempt
def home(req):
    
    req.base_template = "webapp/layout.html"
    return render_to_response('webapp/index.html', context_instance=RequestContext(req))
