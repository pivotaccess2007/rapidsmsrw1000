import csv
from datetime import date, timedelta
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseServerError, HttpResponseRedirect,Http404
from django.template import RequestContext
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404
from django.db import transaction, connection
from django.db.models import Q
from django.db.models import Count,Sum

from rapidsms.webui.utils import *
from reporters.models import *
from reporters.utils import *
from sys import getdefaultencoding
from ubuzima.models import *
from ubuzima.constants import *
from ubuzima.enum import *
from django.contrib.auth.models import *


def cut_date(str):
    stt = [int(x) for x in str.split('.')]
    stt.reverse()
    return date(* stt)
def location_name(req):
    ans = []
    try:
        prv = Location.objects.get(id = int(req.REQUEST['province']))
        ans.append(prv.name + ' Province')
        dst = Location.objects.get(id = int(req.REQUEST['district']))
        ans.append(dst.name + ' District')
        loc = Location.objects.get(id = int(req.REQUEST['loc']))
        ans.append(dst.name)
    except KeyError, DoesNotExist:
        pass
    ans.reverse()
    return ', '.join(ans)

def default_period(req):
    if req.REQUEST.has_key('start_date') and req.REQUEST.has_key('end_date'):
        return {'start':cut_date(req.REQUEST['start_date']),
                  'end':cut_date(req.REQUEST['end_date'])}
    return {'start':date.today()-timedelta(days = datetime.datetime.today().day - 1), 'end':date.today()}

def default_period(req):
    if req.REQUEST.has_key('start_date') and req.REQUEST.has_key('end_date'):
        return {'start':cut_date(req.REQUEST['start_date']),
                  'end':cut_date(req.REQUEST['end_date'])}
    return {'start':date.today()-timedelta(days = datetime.datetime.today().day - 1), 'end':date.today()}#In production
    #return {'start':date.today() - timedelta(date.today().day), 'end':date.today()}#locally

def default_location(req):
    try:
        dst = int(req.REQUEST['district'])
        loc = int(req.REQUEST['location']) if req.REQUEST.has_key('location') else 1
        typ = LocationType.objects.filter(name = 'Health Centre')[0].id
    	uloc=UserLocation.objects.get(user=req.user)
        
        if uloc.location.type == LocationType.objects.filter(name = 'Health Centre')[0]:	return Location.objects.filter(pk = uloc.location.id).extra(select = {'selected':'id = %d' % (loc,)}).order_by('name')
    	else:	return Location.objects.filter(type = typ, district__id = dst).extra(select = {'selected':'id = %d' % (loc,)}).order_by('name')
    except KeyError:
        return []

def default_district(req):
    try:
        par = int(req.REQUEST['province'])
    	uloc=UserLocation.objects.get(user=req.user)
        sel = int(req.REQUEST['district']) if req.REQUEST.has_key('district') else 1
        typ = LocationType.objects.filter(name = 'District')[0].id

        if uloc.location.type == LocationType.objects.filter(name = 'Nation')[0] or uloc.location.type == LocationType.objects.filter(name = 'Province')[0] :  return Location.objects.filter(type = typ, parent__id = par).extra(select = {'selected':'id = %d' % (sel,)}).order_by('name')
    	else:	return Location.objects.filter(pk = uloc.location.district.id).extra(select = {'selected':'id = %d' % (sel,)}).order_by('name')
    except KeyError, IndexError:
        return []

def default_province(req):
    sel = int(req.REQUEST['province']) if req.REQUEST.has_key('province') else 1
    uloc=UserLocation.objects.get(user=req.user)
    try:
        loc = LocationType.objects.filter(name = 'Province')[0].id
    except IndexError:
        return []
    if uloc.location.type == LocationType.objects.filter(name = 'Nation')[0]: return Location.objects.filter(type = loc).extra(select =
        {'selected':'id = %d' % (sel,)}).order_by('name')
    else:	return Location.objects.filter(pk = uloc.location.province.id).extra(select =
        {'selected':'id = %d' % (sel,)}).order_by('name')


#New views for new RapidSMS to track 1000 days

def get_user_location(req):
    try:
        uloc = UserLocation.objects.get(user=req.user)
        return uloc.location
    except UserLocation.DoesNotExist,e:
        return render_to_response(req,"404.html",{'error':e})

def get_params(req):
    return {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}

def get_filters(req, start_key, end_key,loc_key, dst_key, prv_key):
    """ You need to provide the request object, the the date field in database, the location field, the district field in database, and the province field in the database to filter from """
    rez = {}
    diced = get_params(req)
    try:
        rez[start_key] = diced['period']['start']
        rez[end_key] = diced['period']['end']+timedelta(1)
    except KeyError:
        pass
    try:
        loc = int(req.REQUEST['location'])
        rez[loc_key] = loc
    except KeyError:
        if get_user_location(req).type.name == 'Health Centre':   rez[loc_key] =  get_user_location(req).id  
        try:
            dst=int(req.REQUEST['district'])
            rez[dst_key] = dst
        except KeyError:
            if get_user_location(req).type.name == 'District':   rez[dst_key] =  get_user_location(req).id 
            try:
                prv=int(req.REQUEST['province'])
                rez[prv_key] = prv
            except KeyError:
                if get_user_location(req).type.name == 'Province':   rez[prv_key] =  get_user_location(req).id 
                pass

    return rez

def get_loc(req, loc_key, dst_key, prv_key):
    rez = {}
    
    try:
        loc = int(req.REQUEST['location'])
        rez[loc_key] = loc
    except KeyError:
        if get_user_location(req).type.name == 'Health Centre':   rez[loc_key] =  get_user_location(req).id  
        try:
            dst=int(req.REQUEST['district'])
            rez[dst_key] = dst
        except KeyError:
            if get_user_location(req).type.name == 'District':   rez[dst_key] =  get_user_location(req).id 
            try:
                prv=int(req.REQUEST['province'])
                rez[prv_key] = prv
            except KeyError:
                if get_user_location(req).type.name == 'Province':   rez[prv_key] =  get_user_location(req).id 
                pass

    return rez

def get_created(req, start_key, end_key):
    try:
        rez[start_key] = diced['period']['start']
        rez[end_key] = diced['period']['end']+timedelta(1)
    except KeyError:
        pass
    return rez

##Get Registered Report
def get_registered_report(req):
    rez = get_filters(req, start_key = "created__gte", end_key = "created__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Report.objects.filter(**rez)

##Get Registered Deliveries
def get_deliveries(req):
    rez = get_filters(req, start_key = "created__gte", end_key = "created__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Report.objects.filter(type__name = "Birth", **rez)

## Get Registered ANC
def get_anc(req):
    rez = get_filters(req, start_key = "created__gte", end_key = "created__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Report.objects.filter(type__name__in = ["ANC","Pregnancy"], **rez)
## Get Registered PNC
def get_pnc(req):
    rez = get_filters(req, start_key = "created__gte", end_key = "created__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Report.objects.filter(type__name = "PNC", **rez)
## Get Registered Emerging Risk
def get_emerging_risk(req):
    rez = get_filters(req, start_key = "creation__gte", end_key = "creation__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Field.objects.filter(type__category__name = "Risk", report__type__name = "Risk", **rez)
## Get Registered previous Risk
def get_previous_risk(req):
    rez = get_filters(req, start_key = "creation__gte", end_key = "creation__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Field.objects.filter(type__category__name = "Risk", **rez).exclude(report__type__name = "Risk")

## Abagore bari muri progaramu ya Rapidsms
def get_registered_women(req):
    rez = get_loc(req, loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Patient.objects.filter(**rez)

## abavukiye mu rugo
def get_home_dev(req):
    rez = get_filters(req, start_key = "creation__gte", end_key = "creation__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Field.objects.filter(report__type__name = "Birth", type__key = "ho", **rez) 

## abavukiye mu nzira
def get_route_dev(req):
    rez = get_filters(req, start_key = "creation__gte", end_key = "creation__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Field.objects.filter(report__type__name = "Birth", type__key = "or", **rez) 
 
## Abavukiye kwa muganga
def get_facility_dev(req):
    rez = get_filters(req, start_key = "creation__gte", end_key = "creation__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Field.objects.filter(report__type__name = "Birth", type__key__in = ["cl","hp"], **rez)  

##  uko bitabire kwipisha
## kwipisha bwa mbere
def get_anc1_attendees(req):
    rez = get_filters(req, start_key = "created__gte", end_key = "created__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Report.objects.filter(type__name = "Pregnancy", **rez)

## aho kwipisha bwa mbere birangiriye
## kwipisha bwa kabiri
def get_anc2_attendees(req):
    rez = get_filters(req, start_key = "creation__gte", end_key = "creation__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Field.objects.filter(report__type__name = "ANC", type__key = "anc2", **rez)

## aho kwipisha bwa kabiri birangiriye
## kwipisha bwa gatatu
def get_anc3_attendees(req):
    rez = get_filters(req, start_key = "creation__gte", end_key = "creation__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Field.objects.filter(report__type__name = "ANC", type__key = "anc3", **rez)

## aho kwipisha bwa gatatu birangiriye
## kwipisha bwa kane
def get_anc4_attendees(req):
    rez = get_filters(req, start_key = "creation__gte", end_key = "creation__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Field.objects.filter(report__type__name = "ANC", type__key = "anc4", **rez)

## aho kwipisha bwa kane birangiriye

## kwipisha bwa mbere nyuma yo kubyara
def get_pnc1_attendees(req):
    rez = get_filters(req, start_key = "creation__gte", end_key = "creation__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Field.objects.filter(report__type__name = "PNC", type__key = "pnc1", **rez)

## aho kwipisha bwa mbere  nyuma yo kubyara birangiriye
## kwipisha bwa kabiri nyuma yo kubyara
def get_pnc2_attendees(req):
    rez = get_filters(req, start_key = "creation__gte", end_key = "creation__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Field.objects.filter(report__type__name = "PNC", type__key = "pnc2", **rez)

## aho kwipisha bwa kabiri nyuma yo kubyara birangiriye
## kwipisha bwa gatatu nyuma yo kubyara
def get_pnc3_attendees(req):
    rez = get_filters(req, start_key = "creation__gte", end_key = "creation__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Field.objects.filter(report__type__name = "PNC", type__key = "pnc3", **rez)

## aho kwipisha bwa gatatu nyuma yo kubyara birangiriye

## uko bitabira kwipimisha 

##Expectations
##Deliveries
def get_expected_deliveries(req):
    rez = get_filters(req, start_key = "edd_date__gte", end_key = "edd_date__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Report.objects.filter(type__name = "Pregnancy", **rez)
##end of deliveries
##ANC2
def get_expected_anc2(req):
    rez = get_filters(req, start_key = "edd_anc2_date__gte", end_key = "edd_anc2_date__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Report.objects.filter(type__name = "Pregnancy", **rez)
##end of ANC2
##ANC3
def get_expected_anc3(req):
    rez = get_filters(req, start_key = "edd_anc3_date__gte", end_key = "edd_anc3_date__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Report.objects.filter(type__name = "Pregnancy", **rez)
##end of ANC3
##ANC4
def get_expected_anc4(req):
    rez = get_filters(req, start_key = "edd_anc4_date__gte", end_key = "edd_anc4_date__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Report.objects.filter(type__name = "Pregnancy", **rez)
##end of ANC4
##PNC1
def get_expected_pnc1(req):
    rez = get_filters(req, start_key = "edd_pnc1_date__gte", end_key = "edd_pnc1_date__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Report.objects.filter(type__name = "Birth", **rez)
##end of PNC1
##PNC2
def get_expected_pnc2(req):
    rez = get_filters(req, start_key = "edd_pnc2_date__gte", end_key = "edd_pnc2_date__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Report.objects.filter(type__name = "Birth", **rez)
##end of PNC2
##PNC3
def get_expected_pnc3(req):
    rez = get_filters(req, start_key = "edd_pnc3_date__gte", end_key = "edd_pnc3_date__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Report.objects.filter(type__name = "Birth", **rez)
##end of PNC3
## End of expections


##Death
###Get maternal Death 
def get_maternal_death(req):
    rez = get_filters(req, start_key = "creation__gte", end_key = "creation__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Field.objects.filter(type__key = "md", **rez)

###Get Child Death 
def get_child_death(req):
    rez = get_filters(req, start_key = "creation__gte", end_key = "creation__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Field.objects.filter(type__key = "cd", **rez)

###Get New Born Death 
def get_newborn_death(req):
    rez = get_filters(req, start_key = "creation__gte", end_key = "creation__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Field.objects.filter(type__key = "nd", **rez)


##End of Death

##CCM
##Average weight and height of 2 years olds
def get_avg_weight_2years(req):
    period = get_params(req)
    rez = get_filters(req, loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Field.objects.filter(type__key = "child_weight",report__type__name = 'Birth',  report__date__range = (period['period']['end'] - datetime.timedelta(days = 1000), period['period']['end'] - datetime.timedelta(days = 720)), **rez)

def get_avg_height_2years(req):
    period = get_params(req)
    rez = get_filters(req, loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Field.objects.filter(type__key = "child_height",report__type__name = 'Birth',  report__date__range = (period['period']['end'] - datetime.timedelta(days = 1000), period['period']['end'] - datetime.timedelta(days = 720)), **rez)

##Average weight of child at 3rd PNC
def get_avg_weight_pnc3(req):
    period = get_params(req)
    rez = get_filters(req, loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Field.objects.filter(type__key = "child_weight",report__type__name = 'Birth',  report__date__range = (period['period']['start'] - datetime.timedelta(days = Report.DAYS_PNC3), period['period']['end'] - datetime.timedelta(days = Report.DAYS_PNC3)), **rez)

## Mother sick and referred(MR)
def get_mr(req):
    rez = get_filters(req, start_key = "creation__gte", end_key = "creation__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Field.objects.filter(type__key = "mr", **rez)

##Mother and Baby Ok
def get_mbo(req):
    rez = get_filters(req, start_key = "creation__gte", end_key = "creation__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Field.objects.filter(type__key = "mbo", **rez)


##Baby sick and referred (BSR)
def get_bsr(req):
    rez = get_filters(req, start_key = "creation__gte", end_key = "creation__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Field.objects.filter(type__key = "bsr", **rez)



##END OF CCM


##End of New views for new RapidSMS to track 1000 days



###VIEWS RENDERING
@permission_required('ubuzima.can_view')
#@require_GET
@require_http_methods(["GET"])
def index(req,**flts):
    filters = get_params(req)
    reports = get_registered_report(req)
    
    req.session['track']=[
       {'label':'Pregnancy',          'id':'allpreg',
       'number':reports.filter(type=ReportType.objects.get(name = 'Pregnancy')).count()},
       {'label':'Birth',            'id':'bir',
       'number':reports.filter(type=ReportType.objects.get(name = 'Birth')).count()},
        {'label':'ANC',            'id':'anc',
       'number':reports.filter(type=ReportType.objects.get(name = 'ANC')).count()},
       {'label':'Risk', 'id':'risk',
       'number':reports.filter(type=ReportType.objects.get(name = 'Risk')).count()},
       {'label':'Child Health',           'id':'chihe',
       'number':reports.filter(type=ReportType.objects.get(name = 'Child Health')).count()},]
    lox, lxn = 0, location_name(req)
    if req.REQUEST.has_key('location') and req.REQUEST['location'] != '0':
        lox = int(req.REQUEST['location'])
        lxn = Location.objects.get(id = lox)
        lxn=lxn.name+' '+lxn.type.name+', '+lxn.parent.parent.name+' '+lxn.parent.parent.type.name+', '+lxn.parent.parent.parent.name+' '+lxn.parent.parent.parent.type.name
    if req.REQUEST.has_key('csv'):
        heads=['ReportID','Date','Location','Type','Reporter','Patient','Message']
        htp = HttpResponse()
        htp['Content-Type'] = 'text/csv; encoding=%s' % (getdefaultencoding(),)
        wrt = csv.writer(htp, dialect = 'excel-tab')
        seq=[]
        for r in reports:
            try:
                seq.append([r.id, r.created,r.location,r.type,r.reporter.alias,r.patient.national_id, r.summary()])
            except Reporter.DoesNotExist:
                continue
        wrt.writerows([heads]+seq)
        return htp
    else:
        return render_to_response(req,
            "ubuzima/index.html", {'pats':get_registered_women(req).count(),'reps' : get_registered_report(req).count(), 'ho':get_home_dev(req).count(),'or':get_route_dev(req).count(),'hp':get_facility_dev(req).count(),'bi':get_deliveries(req).count(),
            "reports": paginated(req, reports, prefix="rep"),'usrloc':UserLocation.objects.get(user=req.user),'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),
             'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,'locationname':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1]
        })
####END VOEWS RENDERING


