#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

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
from django.template import loader, Context
#############
#from rapidsms.webui.utils import *
from django.template import RequestContext
from django.shortcuts import render_to_response
##############################
from rapidsmsrw1000.apps.reporters.models import *
from rapidsmsrw1000.apps.reporters.utils import *
from sys import getdefaultencoding
from rapidsmsrw1000.apps.ubuzima.models import *
from rapidsmsrw1000.apps.ubuzima.constants import *
from rapidsmsrw1000.apps.ubuzima.newborn_ind import *
from rapidsmsrw1000.apps.ubuzima.enum import *
from django.contrib.auth.models import *
##working with generic view
from django.views.generic import ListView
#from pygrowup.pygrowup import *
from decimal import *

@permission_required('ubuzima.can_view')
#@require_GET
@require_http_methods(["GET"])
def index(req,**flts):
    try:
        p = UserLocation.objects.get(user=req.user)
    except UserLocation.DoesNotExist,e:
        return render_to_response("404.html",{'error':e}, context_instance=RequestContext(req))
    filters = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    reports=matching_reports(req,filters)
    
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
        return render_to_response("index.html", {'pats':get_registered_women(req).count(),'reps' : get_registered_report(req).count(), 'ho':get_home_dev(req).count(),'or':get_route_dev(req).count(),'hp':get_facility_dev(req).count(),'bi':get_deliveries(req).count(),
            "reports": paginated(req, reports, prefix="rep"),'usrloc':UserLocation.objects.get(user=req.user),'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),
             'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,'locationname':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1]
        }, context_instance=RequestContext(req))

@permission_required('ubuzima.can_view')
@require_http_methods(["GET"])
def by_patient(req, pk):
    patient = get_object_or_404(Patient, pk=pk)
    reports = Report.objects.filter(patient=patient).order_by("-created")
    
    # look up any reminders sent to this patient
    reminders = []
    for report in reports:
        for reminder in report.reminders.all():
            reminders.append(reminder)

    return render_to_response(req,
                              "ubuzima/patient.html", { "patient":    patient,
                                                        "reports":    paginated(req, reports, prefix="rep"),
                                                        "reminders":  reminders })
    
@require_http_methods(["GET"])
def by_type(req, pk, **flts):
    report_type = get_object_or_404(ReportType, pk=pk)
    filters = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    reports = matching_reports(req,filters).filter(type=report_type).order_by("-created")
    lox, lxn = 0, location_name(req)
    if req.REQUEST.has_key('location') and req.REQUEST['location'] != '0':
        lox = int(req.REQUEST['location'])
        lxn = Location.objects.get(id = lox)
        lxn=lxn.name+' '+lxn.type.name+', '+lxn.parent.parent.name+' '+lxn.parent.parent.type.name+', '+lxn.parent.parent.parent.name+' '+lxn.parent.parent.parent.type.name
    return render_to_response(req,
                              "ubuzima/type.html", { "type":    report_type,
                                                     "reports":    paginated(req, reports, prefix="rep"),'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),
         'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,'locationname':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1] })
    

@require_http_methods(["GET"])
def view_report(req, pk):
    report = get_object_or_404(Report, pk=pk)
    
    return render_to_response(req,
                              "ubuzima/report.html", { "report":    report })
    
    
@require_http_methods(["GET"])
def by_reporter(req, pk, **flts):
    reporter = Reporter.objects.get(pk=pk)
    filters = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    reports = matching_reports(req,filters).filter(reporter=reporter).order_by("-created")
    lox, lxn = 0, location_name(req)
    if req.REQUEST.has_key('location') and req.REQUEST['location'] != '0':
        lox = int(req.REQUEST['location'])
        lxn = Location.objects.get(id = lox)
        lxn=lxn.name+' '+lxn.type.name+', '+lxn.parent.parent.name+' '+lxn.parent.parent.type.name+', '+lxn.parent.parent.parent.name+' '+lxn.parent.parent.parent.type.name
    return render_to_response(req,
                              "ubuzima/reporter.html", { "reports":    paginated(req, reports, prefix="rep"),
                                                         "reporter":   reporter,'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),
         'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,'locationname':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1] })
@require_http_methods(["GET"])
def by_location(req, pk, **flts):
    location = get_object_or_404(Location, pk=pk)
    filters = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    reports = matching_reports(req,filters).filter(location=location).order_by("-created")
    lox, lxn = 0, location_name(req)
    if req.REQUEST.has_key('location') and req.REQUEST['location'] != '0':
        lox = int(req.REQUEST['location'])
        lxn = Location.objects.get(id = lox)
        lxn=lxn.name+' '+lxn.type.name+', '+lxn.parent.parent.name+' '+lxn.parent.parent.type.name+', '+lxn.parent.parent.parent.name+' '+lxn.parent.parent.parent.type.name
    
    return render_to_response(req,
                              "ubuzima/location.html", { "location":   location,
                                                         "reports":   paginated(req, reports, prefix="rep"),'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),
         'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,'locationname':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1] })
@require_http_methods(["GET"])
def triggers(req):
    triggers = TriggeredText.objects.all()

    current_page = 1
    if 'page' in req.REQUEST:
        current_page = int(req.REQUEST['page'])

    paginator = Paginator(triggers, 25)
    page = paginator.page(current_page)
    
    return render_to_response('ubuzima/triggers.html', dict(triggers=page, paginator=paginator, page=page), context_instance=RequestContext(req) )
    
 
@require_http_methods(["GET"])
def trigger(req, pk):
    trigger = TriggeredText.objects.get(pk=pk)
    return render_to_response(req, 'ubuzima/trigger.html',
            { 'trigger': trigger })

def my_filters(req,diced,alllocs=False):
    rez = {}
    pst = None
    try:
        rez['creation__gte'] = diced['period']['start']
        rez['creation__lte'] = diced['period']['end']+timedelta(1)
    except KeyError:
        pass
    try:
        if alllocs: raise KeyError
        loc = int(req.REQUEST['location'])
        rez['report__location__id'] = loc
    except KeyError:
        try:
            rez['district__id'] = int(req.REQUEST['district'])
        except KeyError:
            try:
                rez['province__id'] = int(req.REQUEST['province'])
            except KeyError:
                pass

    return rez

def my_report_filters(req,diced,alllocs=False):
    rez = {}
    pst = None
    try:
        rez['created__gte'] = diced['period']['start']
        rez['created__lte'] = diced['period']['end']+timedelta(1)
    except KeyError:
        pass
    try:
        if alllocs: raise KeyError
        loc = int(req.REQUEST['location'])
        rez['location__id'] = loc
    except KeyError:
        try:
            rez['district__id'] = int(req.REQUEST['district'])
        except KeyError:
            try:
                rez['province__id'] = int(req.REQUEST['province'])
            except KeyError:
                pass

    return rez 
def my_report_loc(req,diced,alllocs=False):
    rez = {}
    pst = {}
    try:
        if alllocs: raise KeyError
        loc = int(req.REQUEST['location'])
        rez['location__id'] = loc
    except KeyError:
        try:
            dst=int(req.REQUEST['district'])
            #lox = LocationShorthand.objects.filter(district =dst )
            rez['district__id'] = dst#rez['location__in'] = [x.original for x in lox]
        except KeyError:
            try:
                prv=int(req.REQUEST['province'])
                #lox = LocationShorthand.objects.filter(province =prv )
                rez['province__id'] = prv#rez['location__in'] = [x.original for x in lox]
            except KeyError:    pass
    try:
        uloc=UserLocation.objects.get(user=req.user)
        if uloc and uloc.location.type.name=='Health Centre':
            loc=uloc.location.id
            pst['location__id'] = loc
        elif uloc and uloc.location.type.name=='District':   
            dst=uloc.location.id
            #lox = LocationShorthand.objects.filter(district =dst )
            pst['district__id'] = dst#pst['location__in'] = [x.original for x in lox]
        elif uloc and uloc.location.type.name=='Province':
            prv=uloc.location.id  
            #lox = LocationShorthand.objects.filter(province =prv )
            pst['province__id'] = prv#pst['location__in'] = [x.original for x in lox]

    except UserLocation.DoesNotExist:
        pass

    return [rez,pst]
def my_field_loc(req,diced,alllocs=False):
    rez = {}
    pst = {}
    try:
        if alllocs: raise KeyError
        loc = int(req.REQUEST['location'])
        rez['report__location__id'] = loc
    except KeyError:
        try:
            dst=int(req.REQUEST['district'])
            #lox = LocationShorthand.objects.filter(district =dst )
            rez['district__id'] = dst#rez['location__in'] = [x.original for x in lox]
        except KeyError:
            try:
                prv=int(req.REQUEST['province'])
                #lox = LocationShorthand.objects.filter(province =prv )
                rez['province__id'] = prv#rez['location__in'] = [x.original for x in lox]
            except KeyError:    pass
    try:
        uloc=UserLocation.objects.get(user=req.user)
        if uloc and uloc.location.type.name=='Health Centre':
            loc=uloc.location.id
            pst['report__location__id'] = loc
        elif uloc and uloc.location.type.name=='District':   
            dst=uloc.location.id
            #lox = LocationShorthand.objects.filter(district =dst )
            pst['district__id'] = dst#pst['location__in'] = [x.original for x in lox]
        elif uloc and uloc.location.type.name=='Province':
            prv=uloc.location.id  
            #lox = LocationShorthand.objects.filter(province =prv )
            pst['province__id'] = prv#pst['location__in'] = [x.original for x in lox]

    except UserLocation.DoesNotExist:
        pass

    return [rez,pst]
def match_filters(req,diced,alllocs=False):
    rez = {}
    pst = None
    try:
        rez['date__gte'] = diced['period']['start']
        rez['date__lte'] = diced['period']['end']+timedelta(1)
    except KeyError:
        pass
    try:
        if alllocs: raise KeyError
        loc = int(req.REQUEST['location'])
        rez['reporter__location__id'] = loc
    except KeyError:
        try:
            lox = LocationShorthand.objects.filter(district = int(req.REQUEST['district']))
            rez['reporter__location__in'] = [x.original for x in lox]
        except KeyError:
            try:
                lox = LocationShorthand.objects.filter(province = int(req.REQUEST['province']))
                rez['reporter__location__in'] = [x.original for x in lox]
            except KeyError:
                pass

    return rez

def match_filters_fresher(req):
    pst={}
    try:
        uloc=UserLocation.objects.get(user=req.user)
        if uloc and uloc.location.type.name=='Health Centre':
            loc=uloc.location.id
            pst['reporter__location__id'] = loc
        elif uloc and uloc.location.type.name=='District':   
            dst=uloc.location.id
            lox = LocationShorthand.objects.filter(district =dst )
            pst['reporter__location__in'] = [x.original for x in lox]
        elif uloc and uloc.location.type.name=='Province':
            prv=uloc.location.id  
            lox = LocationShorthand.objects.filter(province =prv )
            pst['reporter__location__in'] = [x.original for x in lox]

    except UserLocation.DoesNotExist:
        pass
    return pst

def matching_refusal(req,diced,alllocs=False):
    rez = {}
    pst={}
    try:
        rez['created__gte'] = diced['period']['start']
        rez['created__lte'] = diced['period']['end']+timedelta(1)
    except KeyError:
        pass
    try:
        if alllocs: raise KeyError
        loc = int(req.REQUEST['location'])
        rez['reporter__location__id'] = loc
    except KeyError:
        try:
            lox = LocationShorthand.objects.filter(district = int(req.REQUEST['district']))
            rez['reporter__location__in'] = [x.original for x in lox]
        except KeyError:
            try:
                lox = LocationShorthand.objects.filter(province = int(req.REQUEST['province']))
                rez['reporter__location__in'] = [x.original for x in lox]
            except KeyError:
                pass
    try:
        uloc=UserLocation.objects.get(user=req.user)
        if uloc and uloc.location.type.name=='Health Centre':
            loc=uloc.location.id
            pst['reporter__location__id'] = loc
        elif uloc and uloc.location.type.name=='District':   
            dst=uloc.location.id
            lox = LocationShorthand.objects.filter(district =dst )
            pst['reporter__location__in'] = [x.original for x in lox]
        elif uloc and uloc.location.type.name=='Province':
            prv=uloc.location.id  
            lox = LocationShorthand.objects.filter(province =prv )
            pst['reporter__location__in'] = [x.original for x in lox]

    except UserLocation.DoesNotExist:
        pass

    if rez:
        ans = Refusal.objects.filter(**rez)
    else:
       ans = Refusal.objects.all()

    if pst:
        ans = ans.filter(**pst)
    
    return ans
    

def matching_reports(req, diced, alllocs = False):
    rez = {}
    pst = {}
    try:
        rez['created__gte'] = diced['period']['start']
        rez['created__lte'] = diced['period']['end']+timedelta(1)
    except KeyError:
        pass

    try:
        if alllocs: raise KeyError
        loc = int(req.REQUEST['location'])
        rez['location__id'] = loc
    except KeyError:
        try:
            dst=int(req.REQUEST['district'])
            #lox = LocationShorthand.objects.filter(district =dst )
            rez['district__id'] = dst#rez['location__in'] = [x.original for x in lox]
        except KeyError:
            try:
                prv=int(req.REQUEST['province'])
                #lox = LocationShorthand.objects.filter(province =prv )
                rez['province__id'] = prv#rez['location__in'] = [x.original for x in lox]
            except KeyError:    pass
    try:
        uloc=UserLocation.objects.get(user=req.user)
        if uloc and uloc.location.type.name=='Health Centre':
            loc=uloc.location.id
            pst['location__id'] = loc
        elif uloc and uloc.location.type.name=='District':   
            dst=uloc.location.id
            #lox = LocationShorthand.objects.filter(district =dst )
            pst['district__id'] = dst#pst['location__in'] = [x.original for x in lox]
        elif uloc and uloc.location.type.name=='Province':
            prv=uloc.location.id  
            #lox = LocationShorthand.objects.filter(province =prv )
            pst['province__id'] = prv#pst['location__in'] = [x.original for x in lox]

    except UserLocation.DoesNotExist:
        pass
            
    if rez:
        ans = Report.objects.filter(**rez).order_by("-created")
    else:
       ans = Report.objects.all().order_by("-created")
	
    if pst:
        ans = ans.filter(**pst).order_by("-created")
    return ans

def get_stats_track(req, filters):
    track = {'births':'Birth', 'pregnancy':'Pregnancy','anc':'ANC',
            'childhealth':'Child Health', 'risks': 'Risk','matdeaths':'Maternal Death','chideaths':'Child Death','newbdeaths':'New Born Death'}
    reps=matching_reports(req, filters)
    for k in track.keys():
        dem = reps.filter(type__name =
                track[k]).select_related('patient')
        #if k == 'pregnancy' or k == 'births':
           # dem = set([x.patient.id for x in dem])
        track[k]  = len(dem)
    repgrp        = ReporterGroup.objects.filter(title = 'CHW')
    
    track['chws'] = len(reps.filter(reporter__groups__in = repgrp))
    track['matdeaths']=len(fetch_maternal_death(reps))
    track['chideaths']=len(fetch_child_death(reps))
    track['newbdeaths']=len(fetch_newborn_death(reps))
    return track

@permission_required('ubuzima.can_view')
def view_stats_csv(req, **flts):
    filters = {'period':default_period(req)}
    track = get_stats_track(req, filters)
    rsp   = HttpResponse()
    rsp['Content-Type'] = 'text/csv; encoding=%s' % (getdefaultencoding(),)
    wrt = csv.writer(rsp, dialect = 'excel-tab')
    wrt.writerows([['Births', 'Pregnancy', 'ANC',
        'Child Health', 'Maternal Risks', 'Community Health Workers']] +
        [[track[x] for x in ['births', 'pregnancy','anc', 'childhealth',
            'risks', 'chws']]])
    return rsp

def cut_date(str):
    stt = [int(x) for x in str.split('.')]
    stt.reverse()
    return date(* stt)

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
    

#Reminders Logs! Ceci interroger la base de donnees et presenter a la page nommee remlog.html, toutes les rappels envoyes par le systeme!
@permission_required('ubuzima.can_view')
def view_reminders(req, **flts):
    filters = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    lox, lxn = 0, location_name(req)
    if req.REQUEST.has_key('location') and req.REQUEST['location'] != '0':
        lox = int(req.REQUEST['location'])
        lxn = Location.objects.get(id = lox)
        lxn=lxn.name+' '+lxn.type.name+', '+lxn.parent.parent.name+' '+lxn.parent.parent.type.name+', '+lxn.parent.parent.parent.name+' '+lxn.parent.parent.parent.type.name
    template_name="ubuzima/remlog.html"
    rez=match_filters(req,filters)
    pst=match_filters_fresher(req)
    remlogs=Reminder.objects.filter(**rez).order_by('-date')
    rems_by_type = remlogs.values('type__name','type__pk').annotate(number = Count('id')).order_by('type__name')
    if req.REQUEST.has_key('csv'):
        seq=[]
        htp = HttpResponse()
        htp['Content-Type'] = 'text/csv; encoding=%s' % (getdefaultencoding(),)
        wrt = csv.writer(htp, dialect = 'excel-tab')
        for r in remlogs.filter(**pst):
            try:
                seq.append([r.date, r.type,[r.report.patient if r.report else None],r.reporter.location,r.reporter.connection().identity,["Supervisors: %s,"%str(sup.connection().identity) for sup in r.reporter.reporter_sups()]])
            except Exception: continue
        wrt.writerows([['Date','Type','Patient','Location','Reporter','Supervisor']]+seq)            
        return htp
    else:
        return render_to_response(req, template_name, { "reminders": paginated(req, remlogs.filter(**pst)),'remts': rems_by_type,'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),'usrloc':UserLocation.objects.get(user=req.user),
             'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,'locationname':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1]})

def remlog_by_type(req,pk,**flts):
    filters = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    lox, lxn = 0, location_name(req)
    if req.REQUEST.has_key('location') and req.REQUEST['location'] != '0':
        lox = int(req.REQUEST['location'])
        lxn = Location.objects.get(id = lox)
        lxn=lxn.name+' '+lxn.type.name+', '+lxn.parent.parent.name+' '+lxn.parent.parent.type.name+', '+lxn.parent.parent.parent.name+' '+lxn.parent.parent.parent.type.name
    template_name="ubuzima/remlog.html"
    rem_type=ReminderType.objects.get(pk=pk)
    rez=match_filters(req,filters)
    remlogs=Reminder.objects.filter(type=rem_type,**rez).order_by('-date')
    rems_by_type = remlogs.values('type__name','type__pk').annotate(number = Count('id')).order_by('type__name')
    if req.REQUEST.has_key('csv'):
        seq=[]
        htp = HttpResponse()
        htp['Content-Type'] = 'text/csv; encoding=%s' % (getdefaultencoding(),)
        wrt = csv.writer(htp, dialect = 'excel-tab')
        for r in remlogs:
            try:
                seq.append([r.date, r.type,[r.report.patient if r.report else None],r.reporter.location,r.reporter.connection().identity,["Supervisors: %s,"%str(sup.connection().identity) for sup in r.reporter.reporter_sups()]])
            except Exception: continue
        wrt.writerows([['Date','Type','Patient','Location','Reporter','Supervisor']]+seq)            
        return htp
    else:
        return render_to_response(req, template_name, { "reminders": paginated(req, remlogs),'remts': rems_by_type,'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),'usrloc':UserLocation.objects.get(user=req.user),
         'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,'locationname':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1]})
#End of Reminders Logs!

#Alerts Logs! Ceci interroger la base de donnees et presenter a la page nommee alertlog.html, toutes les rappels envoyes par le systeme!
@permission_required('ubuzima.can_view')
def view_alerts(req, **flts):
    filters = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    lox, lxn = 0, location_name(req)
    if req.REQUEST.has_key('location') and req.REQUEST['location'] != '0':
        lox = int(req.REQUEST['location'])
        lxn = Location.objects.get(id = lox)
        lxn=lxn.name+' '+lxn.type.name+', '+lxn.parent.parent.name+' '+lxn.parent.parent.type.name+', '+lxn.parent.parent.parent.name+' '+lxn.parent.parent.parent.type.name
    template_name="ubuzima/alertlog.html"
    rez=match_filters(req,filters)
    pst=match_filters_fresher(req)
    alertlogs=TriggeredAlert.objects.filter(**rez).order_by('-date')
    triggers = alertlogs.values('trigger__name','trigger__pk').annotate(number = Count('id')).order_by('trigger__name')
    if req.REQUEST.has_key('csv'):
        seq=[]
        htp = HttpResponse()
        htp['Content-Type'] = 'text/csv; encoding=%s' % (getdefaultencoding(),)
        wrt = csv.writer(htp, dialect = 'excel-tab')
        for r in alertlogs.filter(**pst):
            try:
                seq.append([r.date, r.trigger,[r.report.patient if r.report else None],r.reporter.location,r.reporter.connection().identity,["Supervisors: %s,"%str(sup.connection().identity) for sup in r.reporter.reporter_sups()]])
            except Exception: continue
        
        wrt.writerows([['DATE','TRIGGER','PATIENT','LOCATION','REPORTER','SUPERVISOR']]+seq)                   
        return htp
    else:
        return render_to_response(req, template_name, { "alerts": paginated(req, alertlogs.filter(**pst)),'triggers': triggers,'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),'usrloc':UserLocation.objects.get(user=req.user),
             'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,'locationname':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1]})

def alerts_by_type(req,pk,**flts):
    filters = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    lox, lxn = 0, location_name(req)
    if req.REQUEST.has_key('location') and req.REQUEST['location'] != '0':
        lox = int(req.REQUEST['location'])
        lxn = Location.objects.get(id = lox)
        lxn=lxn.name+' '+lxn.type.name+', '+lxn.parent.parent.name+' '+lxn.parent.parent.type.name+', '+lxn.parent.parent.parent.name+' '+lxn.parent.parent.parent.type.name
    template_name="ubuzima/alertlog.html"
    rez=match_filters(req,filters)
    pst=match_filters_fresher(req)
    alertlogs=TriggeredAlert.objects.filter(trigger = pk, **rez).order_by('-date')
    triggers = alertlogs.values('trigger__name','trigger__pk').annotate(number = Count('id')).order_by('trigger__name')
    if req.REQUEST.has_key('csv'):
        seq=[]
        htp = HttpResponse()
        htp['Content-Type'] = 'text/csv; encoding=%s' % (getdefaultencoding(),)
        wrt = csv.writer(htp, dialect = 'excel-tab')
        for r in alertlogs.filter(**pst):
            try:
                seq.append([r.date, r.trigger,[r.report.patient if r.report else None],r.reporter.location,r.reporter.connection().identity,["Supervisors: %s,"%str(sup.connection().identity) for sup in r.reporter.reporter_sups()]])
            except Exception: continue
        
        wrt.writerows([['DATE','TRIGGER','PATIENT','LOCATION','REPORTER','SUPERVISOR']]+seq)                   
        return htp
    else:
        return render_to_response(req, template_name, { "alerts": paginated(req, alertlogs.filter(**pst)),'triggers': triggers,'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),'usrloc':UserLocation.objects.get(user=req.user),
             'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,'locationname':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1]})

#End of Alerts logs


@permission_required('ubuzima.can_view')
def health_indicators(req, flts):
    rez = my_filters(req, flts)
    fields = Field.objects.filter( type__category__name = "Risk", **rez)
    return fields.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description')

def the_chosen(hsh):
    ans = {}
    try:
        ans['province'] = int(hsh['province'])
        ans['district'] = int(hsh['district'])
        ans['location'] = int(hsh['location'])
    except KeyError:
        pass
    return ans

def map_pointers(req, lox, flts):
    dem = []
    try:
        try:
            loc = int(req.REQUEST['location'])
            dem = [Location.objects.get(id = loc).parent]
        except KeyError:
            req.REQUEST['district']
            dem = [x for x in lox if x.longitude]
            if not dem:
                {}['']
    except KeyError:
        pass
    if not dem:
        llv = set([x.location.id for x in matching_reports(req, flts)])
        dem = Location.objects.exclude(longitude = None).filter(id__in = llv).order_by('?')
    return dem[0:10] if len(dem) > 20 else dem

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

def nine_months_ago(months = 9, auj = date.today()):
    ann, moi = auj.year, auj.month - months
    if moi < 1:
        moi = 12 + moi
        ann = ann - 1
    try:
        return date(ann, moi, auj.day)
    except ValueError:
        return date(ann, moi, 28)

def fetch_standards_ancs(qryset):
    ans=[]
    for x in qryset:
        try:  
            if (x.created.date() - x.date) < datetime.timedelta(140):
                ans.append(x)
        except: continue
    return ans

def fetch_edd_info(qryset, start, end):
    edd_start,edd_end=Report.calculate_last_menses(start),Report.calculate_last_menses(end)
    dem  = Report.objects.filter(type = ReportType.objects.get(name = 'Pregnancy'), date__gte =
            edd_start, date__lte = edd_end,location__in=qryset.values('location')).select_related('patient')
    return dem
def fetch_edd(start, end):
    edd_start,edd_end=Report.calculate_last_menses(start),Report.calculate_last_menses(end)
    dem  = Report.objects.filter(type = ReportType.objects.get(name = 'Pregnancy'), date__gte =
            edd_start, date__lte = edd_end).select_related('patient')
    return dem

def fetch_underweight_kids(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'child_weight'), value__lt = str(2.5) )).distinct()
def fetch_boys_kids(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'bo') )).distinct()
def fetch_girls_kids(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'gi') )).distinct()
def fetch_home_deliveries(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'ho') )).distinct()

def fetch_hosp_deliveries(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type__in=FieldType.objects.filter(key__in = ['hp','cl']) )).distinct()

def fetch_en_route_deliveries(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'or') )).distinct()
def fetch_unknown_deliveries(qryset):
    return qryset.exclude(fields__in=Field.objects.filter(type__in=FieldType.objects.filter(key__in = ['hp','cl','ho','or']) )).distinct()

def fetch_anc2_info(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'anc2'))).distinct()

def fetch_anc3_info(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'anc3'))).distinct()

def fetch_anc4_info(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'anc4'))).distinct()

def fetch_ancdp_info(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'dp'))).distinct()

class Gatherer:
    them   = {}
    qryset = None

    def __init__(self, qs):
        self.qryset = qs
        self.pull_from_db()

    def pull_from_db(self):
        rpt = ReportType.objects.get(name = 'Birth')
        prg = ReportType.objects.get(name = 'Pregnancy')
        mas = [x.patient.id for x in self.qryset.filter(type = rpt)]
        for m in self.qryset.filter(type = prg, patient__id__in = mas):
            self.append(m.patient.id, m)
        return

    def append(self, x, y):
        if self.them.has_key(x):
            self.them[x].add(y)
        else:
            self.them[x] = set()
            return self.append(x, y)
        return self

    def distinguish(self):
        stds, nstd = [], []
        for x in self.them.keys():
            if len(self.them[x]) > 3:
                stds.append(self.them[x])
            else:
                nstd.append(self.them[x])
        return (stds, nstd)

def anc_info(qryset):
    return Gatherer(qryset).distinguish()

def fetch_standard_ancs(qryset):
    return Gatherer(qryset).distinguish()[0]

def fetch_nonstandard_ancs(qryset):
    return Gatherer(qryset).distinguish()[1]

def get_patients(qryset):
    pats=set()
    for rep in qryset:
        pats.add(rep.patient)
    return pats

def fetch_anc1_info(qryset):
    return qryset.filter(type=ReportType.objects.get(name = 'Pregnancy'))

def fetch_all4ancs_info(qryset,jour):
    rps=Report.objects.filter(patient__in=Patient.objects.filter(id__in=fetch_anc4_info(qryset).values_list('patient')),type__name__in\
                    =["Pregnancy","ANC"],date__gte=nine_months_ago(9, jour))
    return Patient.objects.filter(id__in=fetch_anc3_info(rps).values_list('patient'))&Patient.objects.filter(id__in=fetch_anc2_info(rps)\
                                            .values_list('patient'))&Patient.objects.filter(id__in=fetch_anc1_info(rps).values_list('patient'))

def fetch_maternal_death(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'md'))).distinct()

def fetch_child_death(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'cd'))).distinct()

def fetch_newborn_death(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'nd'))).distinct()

def fetch_vaccinated_info(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type__in = FieldType.objects.filter(category=FieldCategory.objects.get(name='Vaccination')))).distinct()

def fetch_vaccinated_stats(reps):
    track={}
    for r in FieldType.objects.filter(category=FieldCategory.objects.get(name='Vaccination')): track[r.key]=reps.filter(fields__in = Field.objects.filter(type=FieldType.objects.get(key=r.key))).distinct()
    return track

def fetch_high_risky_preg(qryset):    
    return qryset.filter(fields__in = Field.objects.filter(type__in = FieldType.objects.filter(key__in =['ps','ds','sl','ja','fp','un','sa','co','he','pa','ma','sc','la'])))

def fetch_without_toilet(qryset):
    return qryset.filter(fields__in = Field.objects.filter(type = FieldType.objects.get(key ='nt')))

def fetch_without_hw(qryset):
    return qryset.filter(fields__in = Field.objects.filter(type = FieldType.objects.get(key ='nh')))

def get_important_stats(req, flts):
    resp=pull_req_with_filters(req)
    annot = resp['annot_l']
    locs = resp['locs']
    rez = {}
    
    if resp['sel'].type.name == 'Health Centre':    rez ['location'] = resp['sel']
    else:   rez['%s__in'%annot.split(',')[1]] = [l.pk for l in locs]
    rpt    = ReportType.objects.get(name = 'Birth')
    regula = matching_reports(req, flts)
    qryset = regula.filter(type = rpt).select_related('patient')
    ans    = [
   {'label':'Expected deliveries ',          'id':'expected',
   'number':len(fetch_edd(flts['period']['start'], flts['period']['end']).filter(**rez))},
   {'label':'Underweight Births',           'id':'underweight',
   'number':len(fetch_underweight_kids(qryset))},
   {'label':'Delivered at Home',            'id':'home',
   'number':len(fetch_home_deliveries(qryset))},
   {'label':'Delivered at Health Facility', 'id':'facility',
   'number':len(fetch_hosp_deliveries(qryset))},
   {'label':'Delivered en route',           'id':'enroute',
	'number':len(fetch_en_route_deliveries(qryset))},
    {'label':'Delivered Unknown',           'id':'unknown',
   'number':len(fetch_unknown_deliveries(qryset))}
   ]
    return ans

#View Stats by reports and on Graph view

#Risks Stats
def risk_details(req,**flts):
    filters   = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    details=[]
    tf={}
    ftr=FieldType.objects.filter(category=FieldCategory.objects.get(name='Risk'))
    reps=matching_reports(req, filters).filter(type=ReportType.objects.get(name = 'Risk'))
    lxn,crd = location_name(req), map_pointers(req,
            filters['location'], filters)
    for f in ftr:
        tf[f.key]={}
        ans=[]
        for r in reps:
            try:
                fs=r.fields.filter(type=f)
                if fs:  ans.append(r)
            except Field.DoesNotExist:  pass 
        tf[f.key]={'id':f.key,'label':f.description,'reports':ans}
        details.append(tf[f.key])
                             
            
    return render_to_response(req, 'ubuzima/risk.html',
           {'track':details, 'filters':filters,
         'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),'usrloc':UserLocation.objects.get(user=req.user),
         'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),
           'locationname':lxn,'coords':crd,'stattitle':'Risk Statistics',
           'postqn':(req.get_full_path().split('?', 2) + [''])[1]})

def risk_stats(req,format,dat):
    filters   = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    rez=[]
    f=FieldType.objects.get(key=dat)
    reps=matching_reports(req, filters).filter(type=ReportType.objects.get(name = 'Risk'))
    lxn,crd = location_name(req), map_pointers(req,
            filters['location'], filters)
    for r in reps:
            try:
                fs=r.fields.filter(type=f)
                if fs:  rez.append(r)
            except Field.DoesNotExist:  pass 
        
    if format == 'csv':
        seq=[]
        heads=['ReportID','Reporter', 'Location', 'Patient','ReportDetails','ExpectedDueDate','Supervisors']
        htp = HttpResponse()
        htp['Content-Type'] = 'text/csv; encoding=%s' % (getdefaultencoding(),)
        wrt = csv.writer(htp, dialect = 'excel-tab')
        for r in rez:
            try: seq.append([r.id, r.reporter.connection().identity, r.location,
            r.patient,r.summary(), r.reporter.reporter_sups()])
            except Exception: continue
        wrt.writerows([heads]+seq)
        return htp
    else:
        return render_to_response(req, ('ubuzima/riskdetails.html'),
    {'reports':paginated(req, rez, prefix = 'imp'),'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),'usrloc':UserLocation.objects.get(user=req.user),
         'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,
           'locationname':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1],
   'stattitle': {f.key:f.description,
     }[dat]})    


#End of Risks Stats

#Pregnancy stats

@permission_required('ubuzima.can_view')
def view_pregnancy(req, **flts):
    filters   = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
   
    pregs = matching_reports(req, filters).filter(type=ReportType.objects.get(name = 'Pregnancy'))
    
    lxn,crd = location_name(req), map_pointers(req,
            filters['location'], filters)
    ans    = [
   {'label':'Total Pregnancy Reports',          'id':'allpreg',
   'number':len(pregs)},
   {'label':'High Risk Pregnancies',            'id':'hrpreg',
   'number':len(fetch_high_risky_preg(pregs))},
   {'label':'Pregnant without Toilet', 'id':'notoi',
   'number':len(fetch_without_toilet(pregs))},
   {'label':'Pregnant without Hand Washing station',           'id':'nohw',
   'number':len(fetch_without_hw(pregs))},
    
   ]

    return render_to_response(req, 'ubuzima/pregnancy.html',
           {'track':ans, 'filters':filters,
         'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),'usrloc':UserLocation.objects.get(user=req.user),
         'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),
           'locationname':lxn,'coords':crd,
           'postqn':(req.get_full_path().split('?', 2) + [''])[1]})

@permission_required('ubuzima.can_view')
def pregnancy_stats(req, format, dat):
    flts   = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}

    lxn = location_name(req)

    pregs = matching_reports(req, flts).filter(type=ReportType.objects.get(name = 'Pregnancy'))

    rez = []
    if dat=='allpreg':
        rez=pregs
    elif dat=='hrpreg':
        rez=fetch_high_risky_preg(pregs)
    elif dat=='notoi':
        rez=fetch_without_toilet(pregs)
    elif dat=='nohw':
        rez=fetch_without_hw(pregs)
    
    if format == 'csv':
        seq=[]
        heads=['ReportID','Reporter', 'Location', 'Patient','ReportDetails','ExpectedDueDate','Supervisors']
        htp = HttpResponse()
        htp['Content-Type'] = 'text/csv; encoding=%s' % (getdefaultencoding(),)
        wrt = csv.writer(htp, dialect = 'excel-tab')
        for r in rez:
            try: seq.append([r.id, r.reporter.connection().identity, r.location,
            r.patient,r.summary(), r.show_edd(), r.reporter.reporter_sups()] )
            except Exception: continue
        wrt.writerows([heads]+seq)
        return htp
    else:
        return render_to_response(req, ('ubuzima/pregnancydetails.html'),
    {'reports':paginated(req, rez, prefix = 'imp'),'start_date':date.strftime(flts['period']['start'], '%d.%m.%Y'),'usrloc':UserLocation.objects.get(user=req.user),
         'end_date':date.strftime(flts['period']['end'], '%d.%m.%Y'),'filters':flts,
           'locationname':lxn,
   'stattitle': {'allpreg':'All Pregnancies','hrpreg':'High Risk Pregnancies',
          'notoi':'Pregnant  without Toilet',
                 'nohw':'Pregnant without Hand Washing station',
     }[dat]})


#end of pregnancy stats



#DEATH stats

def view_death(req, **flts):
    filters   = {'period':default_period(req),
                 'location':default_location(req),
                 'province':default_province(req),
                 'district':default_district(req)}

    reps = matching_reports(req, filters)
    chi_deaths = fetch_child_death(reps)
    mo_deaths = fetch_maternal_death(reps)
    nb_deaths = fetch_newborn_death(reps)
    lxn,crd = location_name(req), map_pointers(req,filters['location'], filters)
    ans=[{'label':'Maternal Death',          'id':'matde',
       'number':len(mo_deaths)},
       {'label':'Child Death',           'id':'chide',
       'number':len(chi_deaths)},{'label':'New Born Death',           'id':'newb',
       'number':len(nb_deaths)}]  
    
    return render_to_response(req, 'ubuzima/death.html',
           {'track':ans,'stat':{'matde':len(mo_deaths),'chide':len(chi_deaths),'newb':len(nb_deaths)}, 'filters':filters,'usrloc':UserLocation.objects.get(user=req.user),
         'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),
         'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),
           'locationname':lxn,'coords':crd,
           'postqn':(req.get_full_path().split('?', 2) + [''])[1]}) 


def death_stats(req, format, dat):
    flts   = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    lxn = location_name(req)
    reps = matching_reports(req, flts)
    rez = []
    if dat=='matde':
        rez=fetch_maternal_death(reps)
    elif dat=='chide':
        rez=fetch_child_death(reps)
    elif dat=='newb':
        rez=fetch_newborn_death(reps)
    if format == 'csv':
        seq=[]
        heads=['ReportID','Reporter', 'Location', 'Patient','ReportDetails','Supervisors']
        htp = HttpResponse()
        htp['Content-Type'] = 'text/csv; encoding=%s' % (getdefaultencoding(),)
        wrt = csv.writer(htp, dialect = 'excel-tab')
        for r in rez:
            try: seq.append([r.id, r.reporter.connection().identity, r.location,
            r.patient,r.summary(), r.reporter.reporter_sups()] )
            except Exception: continue
        wrt.writerows([heads]+seq)
        return htp
    else:
        return render_to_response(req, ('ubuzima/deathdetails.html'),
    {'reports':paginated(req, rez, prefix = 'imp'),'start_date':date.strftime(flts['period']['start'], '%d.%m.%Y'),'usrloc':UserLocation.objects.get(user=req.user),
         'end_date':date.strftime(flts['period']['end'], '%d.%m.%Y'),
           'locationname':lxn,
   'stattitle': {'matde':'Maternal Death','chide':'Child Death','newb':'New Born Death', }[dat]})

#end of DEATH stats

#CHILD HEALTH stats
@permission_required('ubuzima.can_view')
def view_chihe(req, **flts):
    filters   = {'period':default_period(req),
                 'location':default_location(req),
                 'province':default_province(req),
                 'district':default_district(req)}

    chihe_reps =matching_reports(req, filters).filter(type = ReportType.objects.get(name = 'Child Health')).select_related('fields')
    vac_chihe_reps=fetch_vaccinated_stats(fetch_vaccinated_info(chihe_reps))
    lxn,crd = location_name(req), map_pointers(req,filters['location'], filters)

    ans=[]
    for v in vac_chihe_reps.keys():
        ans.append({'label':"Children vaccinated with %s"%v,'id':'%s'%v,'number':len(vac_chihe_reps[v])})   
    ans.append({'label':"ALL Children vaccinated ",'id':'all','number':len(fetch_vaccinated_info(chihe_reps))})
    return render_to_response(req, 'ubuzima/chihe.html',
           {'track':ans, 'filters':filters,
         'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),'usrloc':UserLocation.objects.get(user=req.user),
         'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),
           'locationname':lxn,'coords':crd,
           'postqn':(req.get_full_path().split('?', 2) + [''])[1]})

def chihe_stats(req, format, dat):
    flts   = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}

    chihe_reps =matching_reports(req, flts).filter(type = ReportType.objects.get(name = 'Child Health')).select_related('fields')
    vac_chihe_reps=fetch_vaccinated_stats(fetch_vaccinated_info(chihe_reps))    
    lxn = location_name(req)
    rez = []
    for v in vac_chihe_reps.keys():        
        if dat=='%s'%v:
            rez=vac_chihe_reps[v]
    if dat=='all':
        rez=fetch_vaccinated_info(chihe_reps)
    
    if format == 'csv':
        seq=[]
        heads=['ReportID','Reporter', 'Location', 'Patient','ReportDetails','Supervisors']
        htp = HttpResponse()
        htp['Content-Type'] = 'text/csv; encoding=%s' % (getdefaultencoding(),)
        wrt = csv.writer(htp, dialect = 'excel-tab')
        for r in rez:
            try: seq.append([r.id, r.reporter.connection().identity, r.location,
            r.patient,r.summary(), r.reporter.reporter_sups()] )
            except Exception: continue
        wrt.writerows([heads]+seq)
        return htp
    else:
        return render_to_response(req, ('ubuzima/chihedetails.html'),
    {'reports':paginated(req, rez, prefix = 'imp'),'start_date':date.strftime(flts['period']['start'], '%d.%m.%Y'),'usrloc':UserLocation.objects.get(user=req.user),
         'end_date':date.strftime(flts['period']['end'], '%d.%m.%Y'),
           'locationname':lxn,
   'stattitle': {'%s'%dat:'Children Vaccinated with %s'%dat}[dat]})

#end of CHILD HEALTH

#ANC stats
@permission_required('ubuzima.can_view')
def view_anc(req, **flts):
    filters   = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    anc = ReportType.objects.get(name = 'ANC')
    preg= ReportType.objects.get(name = 'Pregnancy')
    reps = matching_reports(req, filters)
    anc_reps =reps.filter(type = anc).select_related('fields')
    preg_reps=reps.filter(type = preg).select_related('fields')
    lxn,crd = location_name(req), map_pointers(req,
            filters['location'], filters)
    ans    = [
   {'label':'Total ANC Reports',          'id':'allanc',
   'number':anc_reps.count()+preg_reps.count()},
   {'label':'Attended First ANC (Pregnancy Registrations)',           'id':'anc1',
   'number':len(preg_reps)}, 
    {'label':'Standard First ANC','id':'stdanc','number':len(fetch_standards_ancs(preg_reps))},
   {'label':'Attended Second ANC',            'id':'anc2',
   'number':len(fetch_anc2_info(anc_reps))},
   {'label':'Attended Third ANC', 'id':'anc3',
   'number':len(fetch_anc3_info(anc_reps))},
   {'label':'Attended Fourth ANC',           'id':'anc4',
   'number':len(fetch_anc4_info(anc_reps))},
    {'label':'Attended all 4 ANCs',           'id':'all4ancs',
       'number':len(fetch_all4ancs_info(anc_reps,filters['period']['end']))},
   {'label':'Departed Patients',          'id':'ancdp',
   'number':len(fetch_ancdp_info(anc_reps))},{'label':'Patients Refused',          'id':'ref',
   'number':len(matching_refusal(req,filters))},
   ]

    return render_to_response(req, 'ubuzima/anc.html',
           {'track':ans,'usrloc':UserLocation.objects.get(user=req.user),'stat':{'ancs':len(anc_reps),'anc1':len(preg_reps),'ref':len(matching_refusal(req,filters)),'stdanc':len(fetch_standards_ancs(preg_reps)),'anc2':len(fetch_anc2_info(anc_reps)),'anc3':len(fetch_anc3_info(anc_reps)),'anc4':len(fetch_anc4_info(anc_reps)),'ancdp':len(fetch_ancdp_info(anc_reps))}, 'filters':filters,
         'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),
         'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),
           'locationname':lxn,'coords':crd,
           'postqn':(req.get_full_path().split('?', 2) + [''])[1]})
 
@permission_required('ubuzima.can_view')
def anc_stats(req, format, dat):
    flts   = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    lxn = location_name(req)
    anc = ReportType.objects.get(name = 'ANC')
    preg= ReportType.objects.get(name = 'Pregnancy')
    reps = matching_reports(req, flts)
    anc_reps =reps.filter(type = anc).select_related('fields')
    preg_reps=reps.filter(type = preg).select_related('fields')
    
    rez = []
    if dat=='anc1':#This is equivalent to Pregnancy reports we have collected within this period!
        rez=preg_reps
    elif dat=='stdanc':
        rez=fetch_standards_ancs(preg_reps)
    elif dat=='anc2':
        rez=fetch_anc2_info(anc_reps)
    elif dat=='anc3':
        rez=fetch_anc3_info(anc_reps)
    elif dat=='anc4':
        rez=fetch_anc4_info(anc_reps)
    elif dat=='ancdp':
        rez=fetch_ancdp_info(anc_reps)
    elif dat=='all4ancs':
        rez=fetch_all4ancs_info(anc_reps,flts['period']['end'])
    elif dat=='allanc':
        rez=anc_reps
    elif dat=='ref':
        return render_to_response(req,('ubuzima/refdetails.html'),{'reports':paginated(req, matching_refusal(req,flts), prefix = 'imp'),'start_date':date.strftime(flts['period']['start'], '%d.%m.%Y'),
         'end_date':date.strftime(flts['period']['end'], '%d.%m.%Y'),'filters':flts,
           'locationname':lxn,
   'stattitle': {'ref':'All Patients Refused',}[dat]})
    if format == 'csv':
        seq=[]
        heads=['ReportID','Reporter', 'Location', 'Patient','IsRisky', 'ReportDetails','ExpectedDueDate','Supervisors']
        htp = HttpResponse()
        htp['Content-Type'] = 'text/csv; encoding=%s' % (getdefaultencoding(),)
        wrt = csv.writer(htp, dialect = 'excel-tab')
        for r in rez:
            try: seq.append([r.id, r.reporter.connection().identity, r.location,
            r.patient,r.is_risky(),r.summary(), r.show_edd(), r.reporter.reporter_sups()] )
            except Exception: 
                try: seq.append([r.id, r.reporter.connection().identity, r.location,
            r.patient,r.is_risky(),r.summary(),None,r.reporter.reporter_sups()] )
                except Exception: continue
        wrt.writerows([heads]+seq)
        return htp
    else:
        return render_to_response(req, ('ubuzima/ancdetails.html'),
    {'reports':paginated(req, rez, prefix = 'imp'),'start_date':date.strftime(flts['period']['start'], '%d.%m.%Y'),'usrloc':UserLocation.objects.get(user=req.user),
         'end_date':date.strftime(flts['period']['end'], '%d.%m.%Y'),'filters':flts,
           'locationname':lxn,
   'stattitle': {'allanc':'All ANC Attendance','anc1':'Attended First ANC (Pregnancy Registrations)','stdanc':'Standard First ANC Visits',
          'anc2':'Attended Second ANC',
                 'anc3':'Attended Third ANC',
             'anc4':'Attended Fourth ANC',
              'ancdp':'Departed Patients','all4ancs':'Attended all 4 ANCs Visits'}[dat]})
    

#end Of ANC!


#End of stats/graph

@permission_required('ubuzima.can_view')
def important_data(req, format, dat):
    flts   = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    rpt    = ReportType.objects.get(name = 'Birth')
    regula = matching_reports(req, flts)
    qryset = regula.filter(type = rpt).select_related('fields')
    rez = []
    if dat == 'expected':
        rez = fetch_edd_info(regula, flts['period']['start'], flts['period']['end'])
    elif dat == 'underweight':
        rez = fetch_underweight_kids(qryset)
    elif dat == 'home':
        rez = fetch_home_deliveries(qryset)
    elif dat == 'facility':
        rez = fetch_hosp_deliveries(qryset)
    elif dat == 'enroute':
        rez = fetch_en_route_deliveries(qryset)
    elif dat=='unknown':
        rez = fetch_unknown_deliveries(qryset)
    elif dat == 'standardanc':
        rez = fetch_standard_ancs(regula)
    elif dat == 'nonstandardanc':
        rez = fetch_nonstandard_ancs(regula)
    if format == 'csv':
        htp = HttpResponse()
        htp['Content-Type'] = 'text/csv; encoding=%s' % (getdefaultencoding(),)
        wrt = csv.writer(htp, dialect = 'excel-tab')
        try: wrt.writerows([[r.id, r.reporter.connection().identity, r.location,
            r.patient, r.created] for r in rez])
        except Exception: wrt.writerows([[r.id, r.reporter, r.location,
            r.patient, r.created] for r in rez])
        return htp
    else:
        return render_to_response(req, ('ubuzima/important.html'),
    {'reports':paginated(req, rez, prefix = 'imp'),'start_date':date.strftime(flts['period']['start'], '%d.%m.%Y'),
         'end_date':date.strftime(flts['period']['end'], '%d.%m.%Y'),
   'stattitle': {'expected':'Expected deliveries in the next 30 days',
          'underweight':'Underweight Births',
                 'home':'Delievered at Home',
             'facility':'Delivered at Health Facility',
              'enroute':'Delivered en route',
                'unknown':'Delivered Unknown',}[dat]})

@permission_required('ubuzima.can_view')
def view_stats(req, **flts):
    filters = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    track   = get_stats_track(req, filters)
    stt = filters['period']['start']
    fin = filters['period']['end']
    lox, lxn, crd = 0, location_name(req), map_pointers(req,
            filters['location'], filters)
    if req.REQUEST.has_key('location') and req.REQUEST['location'] != '0':
        lox = int(req.REQUEST['location'])
        lxn = Location.objects.get(id = lox)
    return render_to_response(req, 'ubuzima/stats.html',
           {'track':track, 'filters':filters,'usrloc':UserLocation.objects.get(user=req.user),
       'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),
         'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),
           'coords':crd, 'location': lox, 'locationname':lxn,
           'chosen':the_chosen(req.REQUEST),
        'important':get_important_stats(req, filters),
           'postqn':(req.get_full_path().split('?', 2) + [''])[1]})

@permission_required('ubuzima.can_view')
def view_indicator(req, indic, format = 'html'):
    resp=pull_req_with_filters(req)
    filters = resp['filters']
    rez = my_filters(req, filters)
    indicator = FieldType.objects.get(id = indic) 
    pts = Field.objects.filter( type = indicator, **rez)
    heads   = ['Reporter', 'Location', 'Patient', 'Type', 'Date']
    resp['headers'] = heads
    resp['reports'] = paginated(req, pts, prefix = 'ind')
    end = resp['filters']['period']['end']
    start = resp['filters']['period']['start']
    annot = resp['annot_l']
    ans_l, ans_m = {},{}
    if format == 'csv':
        rsp = HttpResponse()
        rsp['Content-Type'] = 'text/csv; encoding=%s' % (getdefaultencoding(),)
        wrt = csv.writer(rsp, dialect = 'excel-tab')
        fc = []
        for x in pts:
            try:    fc.append([x.report.reporter.connection().identity, x.report.location, x.report.patient, x.report.type, x.report.created])
            except: continue
        
        wrt.writerows([heads]+fc)
        
        return rsp
    if pts.exists(): 
        pts_l = pts.values("report__"+annot.split(',')[0],"report__"+annot.split(',')[1]).annotate(number=Count('id')).order_by("report__"+annot.split(',')[0])

        ans_l = {'pts' : pts_l, 'tot':pts.values("report__"+annot.split(',')[0],"report__"+annot.split(',')[1]).annotate(number=Count('id')).order_by("report__"+annot.split(',')[0])}

        pts_m = pts.extra(select={'year': 'EXTRACT(year FROM creation)','month': 'EXTRACT(month FROM creation)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')

        ans_m = {'pts' : pts_m, 'tot': pts.extra(select={'year': 'EXTRACT(year FROM creation)','month': 'EXTRACT(month FROM creation)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')}

    resp['track'] = {'items_l':ans_l, 'items_m':ans_m, 'months' : months_between(start,end), 'indicator': indicator}
    return render_to_response(req, ('ubuzima/indicator.html'), resp)

@permission_required('ubuzima.can_view')
def view_stats_reports_csv(req):
    filters = {'period':default_period(req),
             'location':default_location(req)}
    reports = matching_reports(req, filters).order_by('-created')
    seq=[]
    rsp     = HttpResponse()
    rsp['Content-Type'] = 'text/csv; encoding=%s' % (getdefaultencoding(),)
    wrt = csv.writer(rsp, dialect = 'excel-tab')
    for r in reports:
        try: seq.append([r.created, r.reporter.connection().identity, r.location.name, str(r)])
        except Exception: continue
    wrt.writerows(seq)
    return rsp

def has_location(d, loc):
    try:
        lox = Location.objects.filter(parent__parent__parent = d, type__id = 5)
        for l in lox:
            if l.id == loc.id: return d
            a2 = has_location(l, loc)
            if a2: return a2
    except Location.DoesNotExist:
        pass
    return None

def district_and_province(loc, prov):
    dsid = LocationType.objects.get(name = 'District')
    for p in prov:
        dist = Location.objects.filter(type = dsid, parent = p)
        for d in dist:
            l = has_location(d, loc)
            if l: return (p, d)
    return None

@permission_required('ubuzima.can_view')
def shorthand_locations(__req):
    already = LocationShorthand.objects.all()
    newlocs = Location.objects.exclude(id__in = [int(x.original.id) for x in already])
    prid = LocationType.objects.get(name = 'Province')
    prov = Location.objects.filter(type = prid)
    for loc in newlocs:
        got = district_and_province(loc, prov)
        if not got: continue
        prv, dst = got
        ls = LocationShorthand(original = loc, district = dst, province = prv)
        ls.save()
    return HttpResponseRedirect('/ubuzima/stats')

@permission_required('ubuzima.can_view')
def error_display(req):
    them = ErrorNote.objects.all().order_by('-created')
    return render_to_response(req, 'ubuzima/errors.html',
            {'errors':paginated(req, them, prefix = 'err')})
@permission_required('ubuzima.can_view')
def agstats(req, **flts):
    filters = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    reps=matching_reports(req,filters)#all reports filtered
    woas=reps.values_list('location', flat=True).distinct()#all working areas(hc)
    lshs=LocationShorthand.objects.filter(original__in=woas) #all working shorthands



    agsts={}
    outsts=[]
    for hc in lshs:
	            #agsts[prv.id][dst.id][hc.id]={}
	            #agsts[prv.id][dst.id][hc.id]=reps.filter(location=hc)
	            sts={'birth':len(reps.filter(location=hc.original,type__name='Birth')),'pregnancy':len(reps.filter(location=hc.original,type__name='Pregnancy')),'anc':len(reps.filter(location=hc.original,type__name='ANC')),'chihe':len(reps.filter(location=hc.original,type__name='Child Health')),'risk':len(reps.filter(location=hc.original,type__name='Risk')),'matdeaths':len(fetch_maternal_death(reps.filter(location=hc.original))),'chideaths':len(fetch_child_death(reps.filter(location=hc.original))),'newbdeaths':len(fetch_newborn_death(reps.filter(location=hc.original))),'tot':len(reps.filter(location=hc.original)),'prv':hc.province.name,'dst':hc.district.name,'hc':hc.original.name}
	            outsts.append(sts)
    #print outsts
    lxn= location_name(req)
    return render_to_response(req, 'ubuzima/aggstats.html',
               {'track':paginated(req, outsts, prefix = 'imp'), 'filters':filters,
             'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),'usrloc':UserLocation.objects.get(user=req.user),
             'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),
               'locationname':lxn,
               'postqn':(req.get_full_path().split('?', 2) + [''])[1]})
@permission_required('ubuzima.can_view')
def agstats_csv(req):
    filters = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    reps=matching_reports(req,filters)#all reports filtered
    woas=reps.values_list('location', flat=True).distinct()#all working areas(hc)
    lshs=LocationShorthand.objects.filter(original__in=woas) #all working shorthands



    agsts={}
    outsts=[]
    for hc in lshs:
	            #agsts[prv.id][dst.id][hc.id]={}
	            #agsts[prv.id][dst.id][hc.id]=reps.filter(location=hc)
	            sts={'birth':len(reps.filter(location=hc.original,type__name='Birth')),'pregnancy':len(reps.filter(location=hc.original,type__name='Pregnancy')),'anc':len(reps.filter(location=hc.original,type__name='ANC')),'chihe':len(reps.filter(location=hc.original,type__name='Child Health')),'risk':len(reps.filter(location=hc.original,type__name='Risk')),'matdeaths':len(fetch_maternal_death(reps.filter(location=hc.original))),'chideaths':len(fetch_child_death(reps.filter(location=hc.original))),'newbdeaths':len(fetch_newborn_death(reps.filter(location=hc.original))),'tot':len(reps.filter(location=hc.original)),'prv':hc.province.name,'dst':hc.district.name,'hc':hc.original.name}
	            outsts.append(sts)
    heads   = ['Province', 'District', 'Health Centre', 'Birth', 'Pregnancy','ANC','Child Health', 'Risk', 'Maternal Death','Child Death','New Born Death','Total']
    rsp     = HttpResponse()
    rsp['Content-Type'] = 'text/csv; encoding=%s' % (getdefaultencoding(),)
    wrt = csv.writer(rsp, dialect = 'excel-tab')
    wrt.writerows([heads]+[[r['prv'], r['dst'], r['hc'], r['birth'], r['pregnancy'], r['anc'], r['chihe'], r['risk'], r['matdeaths'], r['chideaths'], r['newbdeaths'], r['tot']] for r in outsts])
    return rsp


@permission_required('ubuzima.can_view')
def dash(req):
    resp=pull_req_with_filters(req)
    resp['reports'] = paginated(req, matching_reports(req,resp['filters']), prefix="rep")
    return render_to_response(req,
            "ubuzima/dash.html", resp)
    

def child_locs(loc,filters):
    if loc.type.name == "Nation": return Location.objects.filter(parent=loc)
    elif loc.type.name == "Province": return filters['district'] if filters['district'] else Location.objects.filter(id__in =\
                                            LocationShorthand.objects.filter(province=loc).values_list('original'), type__name='Health Centre').order_by('name')
    elif loc.type.name == "District": return filters['location'] if filters['location'] else Location.objects.filter(id__in = LocationShorthand.objects.filter\
                                                                             (district=loc).values_list('original'), type__name='Health Centre').order_by('name')
    elif loc.type.name == "Health Centre": return filters['location'] if filters['location'] else Location.objects.filter(id=loc.id).order_by('name')

def pull_req_with_filters(req):
    try:
        p = UserLocation.objects.get(user=req.user)
        sel,prv,dst,lxn=None,None,None,None
        filters = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req),}
        try:    sel,lxn=int(req.REQUEST['location']),LocationShorthand.objects.get(original=Location.objects.get(pk=int(req.REQUEST['location'])))
        except KeyError:
            try:    sel,dst=int(req.REQUEST['district']),Location.objects.get(pk=int(req.REQUEST['district']))
            except KeyError:
                try:    sel,prv=int(req.REQUEST['province']),Location.objects.get(pk=int(req.REQUEST['province']))
                except KeyError:    pass
        if sel: sel=Location.objects.get(pk=sel)
        if not sel: sel = p.location 
        locs=child_locs(sel,filters)
        
        return {'usrloc':UserLocation.objects.get(user=req.user),'locs':locs,'annot':annot_val(sel),'annot_l':annot_locs_val(sel),'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),
             'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,'sel':sel,'prv':prv,'dst':dst,'lxn':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1]}
    except UserLocation.DoesNotExist,e:
        return render_to_response(req,"404.html",{'error':e})

def annot_val(loc):
    if loc.type.name == "Nation": return "location__parent__parent__parent__parent__name,location__parent__parent__parent__parent__pk"
    elif loc.type.name == "Province": return "location__parent__parent__parent__name,location__parent__parent__parent__pk"
    elif loc.type.name == "District": return "location__parent__parent__name,location__parent__parent__pk"
    else: return "location__name,location__pk"

def annot_locs_val(loc):
    if loc.type.name == "Nation": return "location__parent__parent__parent__name,location__parent__parent__parent__pk"
    elif loc.type.name == "Province": return "location__parent__parent__name,location__parent__parent__pk"
    elif loc.type.name == "District": return "location__name,location__pk"
    else: return "location__name,location__pk"

@permission_required('ubuzima.can_view')
def charts(req):
    resp = pull_req_with_filters(req)
    qryset, sel = matching_reports(req,resp['filters']).filter(type__name='Birth'), resp['sel']
    end = resp['filters']['period']['end']
    start = resp['filters']['period']['start']
    
    ans, ans_c = qryset.extra(select={'year': 'EXTRACT(year FROM date)','month': 'EXTRACT(month FROM date)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), None
    
    if qryset.exists():
        boys,girls,unwe,home,fac,route,unk = fetch_boys_kids(qryset),fetch_girls_kids(qryset),fetch_underweight_kids(qryset),\
                            fetch_home_deliveries(qryset),fetch_hosp_deliveries(qryset),fetch_en_route_deliveries(qryset),fetch_unknown_deliveries(qryset)
        fac_c, route_c, home_c, unk_c = fac.extra(select={'year': 'EXTRACT(year FROM date)','month': 'EXTRACT(month FROM date)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), route.extra(select={'year': 'EXTRACT(year FROM date)','month': 'EXTRACT(month FROM date)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), home.extra(select={'year': 'EXTRACT(year FROM date)','month': 'EXTRACT(month FROM date)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'),unk.extra(select={'year': 'EXTRACT(year FROM date)','month': 'EXTRACT(month FROM date)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')

        ans_c = {'fac' : fac_c, 'route' : route_c, 'home': home_c, 'unk': unk_c}

    resp['track'] = {'label':['Boys','Girls','Underweight Births','Delivered at Home','Delivered at Health Facility','Delivered en route','Delivered Unknown'],'items':ans, 'items_c':ans_c, 'months' : months_between(start,end), 'qryset': qryset}
    return render_to_response(req, 'ubuzima/charts.html',
           resp)   


def months_between(start,end):
    months = []
    cursor = start

    while cursor <= end:
        m="%d-%d"%(cursor.month,cursor.year)
        if m not in months:
            months.append(m)
        cursor += timedelta(weeks=1)
    
    return months 

def months_enum():
    months=Enum('Months',JAN = 1, FEB = 2, MAR = 3, APR = 4, MAY = 5, JUN = 6, JUL = 7, AUG = 8, SEP = 9, OCT = 10, NOV = 11, DEC = 12)
    return months


def cut_reps_within_months(reps,start,end):
    months_b = months_between(start,end)
    months_e = months_enum()
    ans = []
    i=0
    for m in months_b:
        i=i+1
        ans.append( { 'month' : "%d,"%i+months_e.getByValue(m[0]).name + "-%d" % m[1] , 'data' : reps.filter( date__month = m[0] , date__year = m[1]).count()}  )
    
    return ans

def cut_births_within_months(births,start,end):
    months_b = months_between(start,end)
    months_e = months_enum()
    ans = []
    i=0
    for m in months_b:
        i=i+1
        ans.append( {'home': births.filter(fields__in=Field.objects.filter(type__key='ho'), date__month = m[0] , date__year = m[1]).count(),'fac': births.filter(fields__in=Field.objects.filter(type__key__in=['hp','cl']), date__month = m[0] , date__year = m[1]).count(),'route': births.filter( fields__in=Field.objects.filter(type__key='or'), date__month = m[0] , date__year = m[1]).count(),'total':births.filter(date__month = m[0] , date__year = m[1]).count(),'month' : "%d,"%i+months_e.getByValue(m[0]).name + "-%d" % m[1]}  )
    
    return ans
###START DEATH TABLES, CHARTS, MAP
@permission_required('ubuzima.can_view')
def death_report(req):

    resp = pull_req_with_filters(req)
    reports = matching_reports(req,resp['filters'])
    qryset = reports.filter(fields__in = Field.objects.filter(type__key__in = ["md","cd","nd"]))
    births = reports.filter(type__name='Birth', date__gte = resp['filters']['period']['start'], date__lte = resp['filters']['period']['end'])
    end = resp['filters']['period']['end']
    start = resp['filters']['period']['start']
    annot = resp['annot_l']
    locs = resp['locs']
    ans_l, ans_m = {},{}
    resp['reports'] = paginated(req, qryset, prefix="rep")
    if qryset.exists():

        matde, chide, nebde = fetch_maternal_death(qryset),fetch_child_death(qryset),fetch_newborn_death(qryset) 
 
        matde_l,chide_l,nebde_l = matde.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), chide.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), nebde.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])

        ans_l = {'matde' : matde_l, 'chide' : chide_l, 'nebde': nebde_l, 'tot': qryset.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]) }

        matde_m, chide_m, nebde_m = matde.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), chide.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), nebde.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')

        ans_m = {'matde' : matde_m, 'chide' : chide_m, 'nebde': nebde_m, 'tot': qryset.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')}

    resp['track'] = {'items_l':ans_l, 'items_m':ans_m, 'months' : months_between(start,end), 'bir_l': births.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), 'bir_m': births.extra(select={'year': 'EXTRACT(year FROM date)','month': 'EXTRACT(month FROM date)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')}
    return render_to_response(req, 'ubuzima/death_report.html',
           resp) 

###END OF DEATH TABLES, CHARTS, MAP

###START RISK TABLES, CHARTS, MAP
@permission_required('ubuzima.can_view')
def risk_report(req):

    resp = pull_req_with_filters(req)
    reports = matching_reports(req,resp['filters'])
    resp['reports'] = reports
    qryset = reports.filter(fields__in = Field.objects.filter(type__in = Field.get_risk_fieldtypes()))
    allpatients = Patient.objects.filter( id__in = reports.values('patient')) 
    end = resp['filters']['period']['end']
    start = resp['filters']['period']['start']
    annot = resp['annot_l']
    resp['reports'] = paginated(req, qryset, prefix="rep")
    ans_l, ans_m = {},{}
    if qryset.exists():
        
        patients = allpatients.filter( id__in = qryset.values('patient'))
        alerts = qryset.filter( id__in = TriggeredAlert.objects.filter( report__in = qryset).values('report'))
        red_patients = patients.filter( id__in = alerts.values('patient'))
        yes_alerts = qryset.filter( id__in = TriggeredAlert.objects.filter( report__in = qryset, trigger__destination = "AMB", response = 'YES').values('report'))
        po_alerts = qryset.filter( id__in = TriggeredAlert.objects.filter( report__in = qryset, trigger__destination__in = ["SUP","DIS"], response = 'PO').values('report'))

        patients_l, alerts_l, red_patients_l, yes_alerts_l, po_alerts_l = patients.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), alerts.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), red_patients.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), yes_alerts.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), po_alerts.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])

        ans_l = {'pats' : patients_l, 'alts' : alerts_l, 'rpats': red_patients_l, 'yalts': yes_alerts_l, 'palts': po_alerts_l, 'tot': qryset.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]) }

        patients_m, alerts_m, red_patients_m, yes_alerts_m, po_alerts_m = qryset.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('patient',distinct = True)).order_by('year','month'), alerts.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), alerts.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('patient',distinct = True)).order_by('year','month'), yes_alerts.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), po_alerts.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')

        ans_m = {'pats' : patients_m, 'alts' : alerts_m, 'rpats': red_patients_m, 'yalts': yes_alerts_m, 'palts': po_alerts_m, 'tot': qryset.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')}

    resp['track'] = {'items_l':ans_l, 'items_m':ans_m, 'months' : months_between(start,end), 'pats_l': allpatients.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), 'pats_m': reports.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('patient',distinct = True)).order_by('year','month')}
    return render_to_response(req, 'ubuzima/risk_report.html',
           resp) 

###END OF RISK TABLES, CHARTS, MAP


##START OF BIRTH TABLES, CHARTS, MAP
@permission_required('ubuzima.can_view')
def birth_report(req):
    resp=pull_req_with_filters(req)
    resp['reports']=matching_reports(req,resp['filters'])
    end = resp['filters']['period']['end']
    start = resp['filters']['period']['start']
    #qryset = resp['reports'].filter(type__name='Birth')
    qryset = resp['reports'].filter(type__name='Birth', date__gte = start, date__lte = end )
    #print qryset.count()
    annot=resp['annot_l']
    locs=resp['locs']
    #print qryset.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])
    ans_l, ans_m = {}, {}
    resp['reports'] = paginated(req, qryset, prefix="rep")
    if qryset.exists(): 
        home,fac,route = fetch_home_deliveries(qryset),fetch_hosp_deliveries(qryset),fetch_en_route_deliveries(qryset)
  
        home_l,fac_l,route_l = home.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), fac.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), route.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])

        ans_l = {'fac' : fac_l, 'route' : route_l, 'home': home_l, 'tot':qryset.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])}

        fac_m, route_m, home_m = fac.extra(select={'year': 'EXTRACT(year FROM date)','month': 'EXTRACT(month FROM date)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), route.extra(select={'year': 'EXTRACT(year FROM date)','month': 'EXTRACT(month FROM date)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), home.extra(select={'year': 'EXTRACT(year FROM date)','month': 'EXTRACT(month FROM date)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')

        ans_m = {'fac' : fac_m, 'route' : route_m, 'home': home_m, 'tot': qryset.extra(select={'year': 'EXTRACT(year FROM date)','month': 'EXTRACT(month FROM date)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')}

    resp['track'] = {'items_l':ans_l, 'items_m':ans_m, 'months' : months_between(start,end)}
    return render_to_response('ubuzima/birth_report.html',
           resp, context_instance=RequestContext(req))
##END OF BIRTH TABLES, CHARTS, MAP

##START OF PREGNANCY TABLES, CHARTS, MAP
@permission_required('ubuzima.can_view')
def preg_report(req):
    
    resp=pull_req_with_filters(req)
    resp['reports']=matching_reports(req,resp['filters'])
    end = resp['filters']['period']['end']
    start = resp['filters']['period']['start']
    preg = resp['reports'].filter(type__name='Pregnancy', date__gte = start, date__lte = end )
    annot = resp['annot_l']
    locs = resp['locs']
    ans_l, ans_m, rez = {}, {}, {}
    rez['%s__in'%annot.split(',')[1]] = [l.pk for l in locs]
    edd = fetch_edd( start, end).filter(** rez)
    resp['reports'] = paginated(req, preg, prefix="rep")
    if preg.exists() or edd.exists(): 
        preg_l, preg_risk_l, edd_l, edd_risk_l = preg.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), fetch_high_risky_preg(preg).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), edd.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), fetch_high_risky_preg(edd).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]) 

        ans_l = {'pre' : preg_l, 'prehr' : preg_risk_l, 'edd': edd_l, 'eddhr': edd_risk_l}

        preg_m, preg_risk_m, edd_m, edd_risk_m = preg.extra(select={'year': 'EXTRACT(year FROM date)','month': 'EXTRACT(month FROM date)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), fetch_high_risky_preg(preg).extra(select={'year': 'EXTRACT(year FROM date)','month': 'EXTRACT(month FROM date)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), edd.extra(select={'year': 'EXTRACT(year FROM date)','month': 'EXTRACT(month FROM date)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'),fetch_high_risky_preg(edd).extra(select={'year': 'EXTRACT(year FROM date)','month': 'EXTRACT(month FROM date)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')

        ans_m = {'pre' : preg_m, 'prehr' : preg_risk_m, 'edd': edd_m, 'eddhr': edd_risk_m}
        
    resp['track'] = {'items_l':ans_l, 'items_m':ans_m, 'months' : months_between(start,end), 'months_edd' : months_between(Report.calculate_last_menses(start),Report.calculate_last_menses(end))}
    return render_to_response(req, 'ubuzima/preg_report.html',
           resp)
##END OF PREGNANCY TABLES, CHARTS, MAP

##START OF ADMIN TABLES, CHARTS, MAP
@permission_required('ubuzima.can_view')
def admin_report(req):
    resp=pull_req_with_filters(req)
    annot = resp['annot_l']
    locs = resp['locs']
    ans_l, ans_m, rez = {}, {}, {}
    rez['%s__in'%annot.split(',')[1]] = [l.pk for l in locs]
    reporters = Reporter.objects.filter(groups__title = 'CHW', ** rez)
    active = reporters.filter(connections__in = PersistantConnection.objects.filter(last_seen__gte = datetime.datetime.today().date() - timedelta(30)))
    resp['reports'] = paginated(req, reporters, prefix="rep")
    if reporters.exists() or active.exists(): 
        reporters_l, active_l = reporters.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), active.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])

        ans_l = {'rep' : reporters_l, 'act' : active_l}
        
    resp['track'] = {'items_l':ans_l}
    return render_to_response(req, 'ubuzima/admin_report.html',
           resp)
##END OF ADMIN TABLES, CHARTS, MAP

##START OF CHILD TABLES, CHARTS, MAP
@permission_required('ubuzima.can_view')
def child_report(req):
    resp=pull_req_with_filters(req)
    resp['reports']=matching_reports(req,resp['filters'])
    end = resp['filters']['period']['end']
    start = resp['filters']['period']['start']
    qryset = resp['reports'].filter(type__name='Birth', date__gte = start, date__lte = end )
    annot=resp['annot_l']
    locs=resp['locs']
    resp['reports'] = paginated(req, qryset, prefix="rep")
    return render_to_response(req, 'ubuzima/child_report.html',
           resp)
##END OF CHILD TABLES, CHARTS, MAP
##START OF CHILD DETAILS TABLES, CHARTS, MAP
@permission_required('ubuzima.can_view')
def child_details_report(req, pk):
    resp=pull_req_with_filters(req)
    birth = Report.objects.get(pk = pk)
    child = birth.get_child()
    resp['reports'] = paginated(req, child['log'], prefix="rep")    
    resp['track'] = child
    return render_to_response(req, 'ubuzima/child_details.html',
           resp)
##END OF CHILD DETAILS TABLES, CHARTS, MAP

###Function to test any template
@permission_required('ubuzima.can_view')
def tests(req,dat):
    resp=pull_req_with_filters(req)
    annot=resp['annot']
    locs=resp['locs']
    qryset,ans=None,[]
    if dat == 'bir': 
        qryset = matching_reports(req,resp['filters']).filter(type__name='Birth')
        if qryset:
            boys,girls,unwe,home,fac,route,unk = fetch_boys_kids(qryset),fetch_girls_kids(qryset),fetch_underweight_kids(qryset),\
                            fetch_home_deliveries(qryset),fetch_hosp_deliveries(qryset),fetch_en_route_deliveries(qryset),fetch_unknown_deliveries(qryset)
            ans = [ 
                    {   'label':['Boys','Girls','Underweight Births','Delivered at Home','Delivered at Health Facility','Delivered en route','Delivered Unknown'],
                        'number':[boys.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]),
                        girls.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]),
                        unwe.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]),
                        home.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]),
                        fac.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]),
                        route.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]),
                        unk.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]),		
                        ],
                        'totals':[boys.count(),girls.count(),unwe.count(),home.count(),fac.count(),route.count(),unk.count()],
                        'totalglobal':qryset.count()
                    }
                ]
        else: pass
    resp['track'] = ans
    resp['lev']=annot.split(',')[0]
    return render_to_response(req, 'ubuzima/test.html',
           resp)


##DASHBOARD 
@permission_required('ubuzima.can_view')
def dashboard(req):
    resp=pull_req_with_filters(req)
    hindics = health_indicators(req,resp['filters'])
    resp['hindics'] = paginated(req, hindics, prefix = 'hind')
    return render_to_response(req,
            "ubuzima/dashboard.html", resp)
##END OF DASHBOARD

def fetch_pnc1_info(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'pnc1'))).distinct()

def fetch_pnc2_info(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'pnc2'))).distinct()

def fetch_pnc3_info(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'pnc3'))).distinct()

def fetch_eddanc2_info(qryset, start, end):
    eddanc2_start,eddanc2_end=Report.calculate_last_menses(start+datetime.timedelta(days=Report.DAYS_ANC2)),Report.calculate_last_menses(end+datetime.timedelta(days=Report.DAYS_ANC2))
    demo  = Report.objects.filter(type = ReportType.objects.get(name = 'Pregnancy'), date__gte =
            eddanc2_start, date__lte = eddanc2_end,location__in=qryset.values('location')).select_related('patient')
    return demo

def fetch_eddanc3_info(qryset, start, end):
    eddanc3_start,eddanc3_end=Report.calculate_last_menses(start+datetime.timedelta(days=Report.DAYS_ANC3)),Report.calculate_last_menses(end+datetime.timedelta(days=Report.DAYS_ANC3))
    demo  = Report.objects.filter(type = ReportType.objects.get(name = 'Pregnancy'), date__gte =
            eddanc3_start, date__lte = eddanc3_end,location__in=qryset.values('location')).select_related('patient')
    return demo

def fetch_eddanc4_info(qryset, start, end):
    eddanc4_start,eddanc4_end=Report.calculate_last_menses(start+datetime.timedelta(days=Report.DAYS_ANC4)),Report.calculate_last_menses(end+datetime.timedelta(days=Report.DAYS_ANC4))
    demo  = Report.objects.filter(type = ReportType.objects.get(name = 'Pregnancy'), date__gte =
            eddanc4_start, date__lte = eddanc4_end,location__in=qryset.values('location')).select_related('patient')
    return demo


###START ANC TABLES, CHARTS, MAP
@permission_required('ubuzima.can_view')
def anc_report(req):
    resp=pull_req_with_filters(req)
    reports = matching_reports(req,resp['filters'])
    resp['reports']=reports
    end = resp['filters']['period']['end']
    start = resp['filters']['period']['start']
    
    qryset=resp['reports'].filter(type__name='ANC')
    ##qryset = resp['reports'].filter(fields__in = Field.objects.filter(type__key__in = ["anc2","anc3","anc4"]))
    preg_reps=resp['reports'].filter(type__name='Pregnancy',date__gte = resp['filters']['period']['start'], date__lte = resp['filters']['period']['end'])
    
    annot=resp['annot_l']
    locs=resp['locs']
    ans_l, ans_m = {},{}
    ans_t = qryset.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')
    

    new_qryset=resp['reports'].filter(type__name= 'Pregnancy',date__gte = start , date__lte = end )
    
    resp['reports'] = paginated(req, qryset, prefix="rep")
    


    if qryset.exists():
        

        anc1_c = preg_reps.extra(select={'year': 'EXTRACT(year FROM date)','month': 'EXTRACT(month FROM date)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')

        anc2_c = fetch_anc2_info(qryset).extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')
        anc3_c = fetch_anc3_info(qryset).extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')
        anc4_c = fetch_anc4_info(qryset).extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')
        eddanc2_c = fetch_eddanc2_info(qryset,start,end).extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')
        eddanc3_c = fetch_eddanc3_info(qryset,start,end).extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')
        eddanc4_c = fetch_eddanc4_info(qryset,start,end).extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')


        ans_m = {'anc1_m' : anc1_c, 'anc2_m' : anc2_c, 'anc3_m': anc3_c, 'anc4_m': anc4_c, 'eddanc2_m': eddanc2_c, 'eddanc3_m': eddanc3_c, 'eddanc4_m': eddanc4_c,'tot_m': qryset.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')}


        anc1_l=preg_reps.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])
        anc2_l=fetch_anc2_info(qryset).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])
        anc3_l=fetch_anc3_info(qryset).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])
        anc4_l=fetch_anc4_info(qryset).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])
        eddanc2_l=fetch_eddanc2_info(qryset,start,end).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])
        eddanc3_l=fetch_eddanc3_info(qryset,start,end).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])
        eddanc4_l = fetch_eddanc4_info(qryset,start,end).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])

        ans_l = {'anc1' : anc1_l, 'anc2' : anc2_l, 'anc3': anc3_l, 'anc4': anc4_l, 'eddanc2': eddanc2_l, 'eddanc3': eddanc3_l, 'eddanc4': eddanc4_l, 'tot':qryset.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])}
        
        

    resp['track'] = {'items':ans_l, 'items_m':ans_m,'items_t':ans_t, 'months' : months_between(start,end)}
    return render_to_response(req, 'ubuzima/anc_report.html',
           resp)  

###END OF ANC TABLES, CHARTS, MAP

###START PNC TABLES, CHARTS, MAP
@permission_required('ubuzima.can_view')
def pnc_report(req):
    resp=pull_req_with_filters(req)
    resp['reports']=matching_reports(req,resp['filters'])
    ##qryset=resp['reports'].filter(type__name='ANC')
    qryset = resp['reports'].filter(fields__in = Field.objects.filter(type__key__in = ["pnc1","pnc2","pnc3"]))
    end = resp['filters']['period']['end']
    start = resp['filters']['period']['start']
    annot=resp['annot_l']
    locs=resp['locs']
    ans_l, ans_m = {},{}
    resp['reports'] = paginated(req, qryset, prefix="rep")
    if qryset.exists():
        pnc1_m,pnc2_m,pnc3_m = fetch_pnc1_info(qryset),fetch_pnc2_info(qryset),fetch_pnc3_info(qryset)

        pnc1_c, pnc2_c, pnc3_c = pnc1_m.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), pnc2_m.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), pnc3_m.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')

        ans_m = {'pnc1_m' : pnc1_c, 'pnc2_m' : pnc2_c, 'pnc3_m': pnc3_c ,'tot_m': qryset.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')}



        pnc1_l= fetch_pnc1_info(qryset).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])
        
        pnc2_l= fetch_pnc2_info(qryset).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])
        pnc3_l= fetch_pnc3_info(qryset).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])

        ans_l = {'pnc1' : pnc1_l, 'pnc2' : pnc2_l, 'pnc3': pnc3_l, 'tot':qryset.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])}
        

    resp['track'] = {'items':ans_l, 'items_m':ans_m, 'months' : months_between(start,end)}
    return render_to_response(req, 'ubuzima/pnc_report.html',resp)  

###END OF PNC TABLES, CHARTS, MAP


###START NUTRITION TABLES, CHARTS, MAP
@permission_required('ubuzima.can_view')
def nutrition_indicators(req, flts):
    rez = my_filters(req, flts)
    pst = my_report_filters(req, flts)
    locz = my_report_loc(req,flts)
    locz1 = my_field_loc(req,flts)
    resp=pull_req_with_filters(req)
    start = resp['filters']['period']['start']
    start_6 = start - timedelta(days = 270-1)
    start_9 = start - timedelta(days = 540-1)
    start_18 = start - timedelta(days = 720-1)
    start_24 = start - timedelta(days = 1000-1)
    end = resp['filters']['period']['end']
    end_6 = end - timedelta(days = 180)
    end_9 = end - timedelta(days = 270)
    end_18 = end - timedelta(days = 540)
    end_24 = end - timedelta(days = 720)

    preg_women = Report.objects.filter( type__name = "Pregnancy",edd_date__gte = resp['filters']['period']['start'] , edd_date__lte = resp['filters']['period']['end'] ,**locz[0]).filter(**locz[1]).count()
    edd_anc3 = Report.objects.filter(type = ReportType.objects.get(name = "Pregnancy"),edd_anc3_date__range = (start,end)  , **locz[0]).filter(**locz[1]).count()
    edd_pnc1 = Report.objects.filter(type = ReportType.objects.get(name = "Birth"),edd_pnc1_date__range = (start,end)  , **locz[0]).filter(**locz[1]).count()
    edd_pnc2 = Report.objects.filter(type = ReportType.objects.get(name = "Birth"),edd_pnc2_date__range = (start,end) , **locz[0]).filter(**locz[1]).count()
    edd_pnc3 = Report.objects.filter(type = ReportType.objects.get(name = "Birth"),edd_pnc3_date__range = (start,end) , **locz[0]).filter(**locz[1]).count()
    total_bir = Report.objects.filter(type = ReportType.objects.get(name = "Birth"), **pst).filter(**locz[1]).count()

    total_bir_6_ago = Report.objects.filter(type = ReportType.objects.get(name = "Birth"), date__range = (start_6,end_6), **locz[0]).filter(**locz[1]).count()
    total_bir_9_ago = Report.objects.filter(type = ReportType.objects.get(name = "Birth"), date__range = (start_9,end_9), **locz[0]).filter(**locz[1]).count()
    total_bir_18_ago = Report.objects.filter(type = ReportType.objects.get(name = "Birth"), date__range = (start_18,end_18), **locz[0]).filter(**locz[1]).count()
    total_bir_24_ago = Report.objects.filter(type = ReportType.objects.get(name = "Birth"), date__range = (start_24,end_24), **locz[0]).filter(**locz[1]).count()

    maternal_risk = Field.objects.filter( type__key = "mother_height", value__lt = str(1.50), **rez).filter(**locz1[1])
    maternal_nutrition = Field.objects.filter( type__key = "bmi", value__lt = str(18.50), **rez).filter(**locz1[1])
    birth_w = Field.objects.filter( type__key = "mother_weight", value__lt = str(2.50), **rez).filter(**locz1[1])
    birth_t = Field.objects.filter( type__key = "te", **rez).filter(**locz1[1])
    vac_dpt3 = Field.objects.filter( type__key = "v3", **rez).filter(**locz1[1])
    vac_measles = Field.objects.filter( type__key = "v5", **rez).filter(**locz1[1])
    ebf1_reps = Field.objects.filter( type__key = "ebf1", **rez).filter(**locz1[1])
    ebf2_reps = Field.objects.filter( type__key = "ebf2", **rez).filter(**locz1[1])
    ebf3_reps = Field.objects.filter( type__key = "ebf3", **rez).filter(**locz1[1])
    ebf4_reps = Field.objects.filter( type__key = "ebf4", **rez).filter(**locz1[1])
    anc3_reps = Field.objects.filter( type__key = "anc3", **rez).filter(**locz1[1])
    pnc1_reps = Field.objects.filter( type__key = "pnc1", **rez).filter(**locz1[1])
    pnc2_reps = Field.objects.filter( type__key = "pnc2", **rez).filter(**locz1[1])
    pnc3_reps = Field.objects.filter( type__key = "pnc3", **rez).filter(**locz1[1])

    anthro_h_6_reps = Field.objects.filter( type__key = "child_height", report__date__range = (start_6,end_6), **rez).filter(**locz1[1])
    anthro_w_6_reps = Field.objects.filter( type__key = "child_weight", report__date__range = (start_6,end_6), **rez).filter(**locz1[1])
    anthro_h_9_reps = Field.objects.filter( type__key = "child_height", report__date__range = (start_9,end_9), **rez).filter(**locz1[1])
    anthro_w_9_reps = Field.objects.filter( type__key = "child_weight", report__date__range = (start_9,end_9), **rez).filter(**locz1[1])
    anthro_h_18_reps = Field.objects.filter( type__key = "child_height", report__date__range = (start_18,end_18), **rez).filter(**locz1[1])
    anthro_w_18_reps = Field.objects.filter( type__key = "child_weight", report__date__range = (start_18,end_18), **rez).filter(**locz1[1])
    anthro_h_24_reps = Field.objects.filter( type__key = "child_height", report__date__range = (start_24,end_24), **rez).filter(**locz1[1])
    anthro_w_24_reps = Field.objects.filter( type__key = "child_weight", report__date__range = (start_24,end_24), **rez).filter(**locz1[1])
    

    stunted_6_reps = anthro_w_6_reps.filter( id__in = [ f.id for f in anthro_w_6_reps if get_my_child_zscores(get_my_child(f.report))['lhfa'] and get_my_child_zscores(get_my_child(f.report))['lhfa'] < -2 ])
    stunted_9_reps = anthro_w_9_reps.filter( id__in = [ f.id for f in anthro_w_9_reps if get_my_child_zscores(get_my_child(f.report))['lhfa'] and get_my_child_zscores(get_my_child(f.report))['lhfa'] < -2 ])
    stunted_18_reps = anthro_w_18_reps.filter( id__in = [ f.id for f in anthro_w_18_reps if get_my_child_zscores(get_my_child(f.report))['lhfa'] and get_my_child_zscores(get_my_child(f.report))['lhfa'] < -2 ])
    stunted_24_reps = anthro_w_24_reps.filter( id__in = [ f.id for f in anthro_w_24_reps if get_my_child_zscores(get_my_child(f.report))['lhfa'] and get_my_child_zscores(get_my_child(f.report))['lhfa'] < -2 ])
    wasted_6_reps = anthro_w_6_reps.filter( id__in = [ f.id for f in anthro_w_6_reps if get_my_child_zscores(get_my_child(f.report))['wfl'] and get_my_child_zscores(get_my_child(f.report))['wfl'] < -2 ])
    wasted_9_reps = anthro_w_9_reps.filter( id__in = [ f.id for f in anthro_w_9_reps if get_my_child_zscores(get_my_child(f.report))['wfl'] and get_my_child_zscores(get_my_child(f.report))['wfl'] < -2 ])
    wasted_18_reps = anthro_w_18_reps.filter( id__in = [ f.id for f in anthro_w_18_reps if get_my_child_zscores(get_my_child(f.report))['wfl'] and get_my_child_zscores(get_my_child(f.report))['wfl'] < -2 ])
    wasted_24_reps = anthro_w_24_reps.filter( id__in = [ f.id for f in anthro_w_24_reps if get_my_child_zscores(get_my_child(f.report))['wfl'] and get_my_child_zscores(get_my_child(f.report))['wfl'] < -2 ])
    unwe_6_reps = anthro_w_6_reps.filter( id__in = [ f.id for f in anthro_w_6_reps if get_my_child_zscores(get_my_child(f.report))['wfa'] and get_my_child_zscores(get_my_child(f.report))['wfa'] < -2 ])
    unwe_9_reps = anthro_w_9_reps.filter( id__in = [ f.id for f in anthro_w_9_reps if get_my_child_zscores(get_my_child(f.report))['wfa'] and get_my_child_zscores(get_my_child(f.report))['wfa'] < -2 ])
    unwe_18_reps = anthro_w_18_reps.filter( id__in = [ f.id for f in anthro_w_18_reps if get_my_child_zscores(get_my_child(f.report))['wfa'] and get_my_child_zscores(get_my_child(f.report))['wfa'] < -2 ])
    unwe_24_reps = anthro_w_24_reps.filter( id__in = [ f.id for f in anthro_w_24_reps if get_my_child_zscores(get_my_child(f.report))['wfa'] and get_my_child_zscores(get_my_child(f.report))['wfa'] < -2 ])
    

    
    indics = {'home':[{'desc': maternal_height, 'fs':  maternal_risk.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered pregnant women " % preg_women, 'patients': maternal_risk},
{'desc': maternal_bmi, 'fs':  maternal_nutrition.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered pregnant women " % preg_women, 'patients': maternal_nutrition}, {'desc': maternal_anc, 'fs':  anc3_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d Expected ANC3 " % edd_anc3, 'reports': anc3_reps },
{'desc': birth_weight, 'fs':  birth_w.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered live births" % total_bir, 'reports': birth_w},
{'desc': birth_term, 'fs':  birth_t.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered live births" % total_bir,  'reports': birth_t},
{'desc': vaccination_dpt3, 'fs':  vac_dpt3.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered births 6 months old " % total_bir_6_ago, 'fields':  vac_dpt3},
{'desc': vaccination_measles, 'fs':  vac_measles.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered births 9 months old " % total_bir_9_ago, 'fields': vac_measles},
{'desc': ebf1, 'fs':  ebf1_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered live births " % total_bir, 'reports': ebf1_reps},
{'desc': ebf2, 'fs':  ebf2_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered live births " % total_bir, 'reports': ebf2_reps},
{'desc': ebf3, 'fs':  ebf3_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered live births " % total_bir, 'reports': ebf3_reps},
{'desc': ebf4, 'fs':  ebf4_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered live births " % total_bir, 'reports': ebf4_reps},
{'desc': pnc1, 'fs':  pnc1_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d Expected PNC1 " % edd_pnc1, 'reports': pnc1_reps},
{'desc': pnc2, 'fs':  pnc2_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d Expected PNC2 " % edd_pnc2, 'reports': pnc2_reps},
{'desc': pnc3, 'fs':  pnc3_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d Expected PNC3 " % edd_pnc3, 'fields': pnc3_reps},
{'desc': anthro_h_6, 'fs':  anthro_h_6_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered births 6 months old " % total_bir_6_ago, 'fields': anthro_h_6_reps},
{'desc': anthro_h_9, 'fs':  anthro_h_9_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered births 9 months old " % total_bir_9_ago, 'fields': anthro_h_9_reps},
{'desc': anthro_h_18, 'fs':  anthro_h_18_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered births 18 months old " % total_bir_18_ago, 'fields': anthro_h_18_reps},
{'desc': anthro_h_24, 'fs':  anthro_h_24_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered births 24 months old " % total_bir_24_ago, 'fields': anthro_h_24_reps},

{'desc': anthro_w_6, 'fs':  anthro_w_6_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered births 6 months old " % total_bir_6_ago, 'fields': anthro_w_6_reps},
{'desc': anthro_w_9, 'fs':  anthro_w_9_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered births 9 months old " % total_bir_9_ago, 'fields': anthro_w_9_reps},
{'desc': anthro_w_18, 'fs':  anthro_w_18_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered births 18 months old " % total_bir_18_ago, 'fields': anthro_w_18_reps},
{'desc': anthro_w_24, 'fs':  anthro_w_24_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered births 24 months old " % total_bir_24_ago, 'fields': anthro_w_24_reps},

{'desc': stunted_6, 'fs':  stunted_6_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered births 6 months old " % total_bir_6_ago, 'fields': stunted_6_reps},
{'desc': stunted_9, 'fs':  stunted_9_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered births 9 months old " % total_bir_9_ago, 'fields': stunted_9_reps},
{'desc': stunted_18, 'fs':  stunted_18_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered births 18 months old " % total_bir_18_ago, 'fields': stunted_18_reps},
{'desc': stunted_24, 'fs':  stunted_24_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered births 24 months old " % total_bir_24_ago, 'fields': stunted_24_reps},

{'desc': wasted_6, 'fs':  wasted_6_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered births 6 months old " % total_bir_6_ago, 'fields': wasted_6_reps},
{'desc': wasted_9, 'fs':  wasted_9_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered births 9 months old " % total_bir_9_ago, 'fields': wasted_9_reps},
{'desc': wasted_18, 'fs':  wasted_18_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered births 18 months old " % total_bir_18_ago, 'fields': wasted_18_reps},
{'desc': wasted_24, 'fs':  wasted_24_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered births 24 months old " % total_bir_24_ago, 'fields': wasted_24_reps},

{'desc': unwe_6, 'fs':  unwe_6_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered births 6 months old " % total_bir_6_ago, 'fields': unwe_6_reps},
{'desc': unwe_9, 'fs':  unwe_9_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered births 9 months old " % total_bir_9_ago, 'fields': unwe_9_reps},
{'desc': unwe_18, 'fs':  unwe_18_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered births 18 months old " % total_bir_18_ago, 'fields': unwe_18_reps},
{'desc': unwe_24, 'fs':  unwe_24_reps.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered births 24 months old " % total_bir_24_ago, 'fields': unwe_24_reps},


], 'desc': { '%s'%maternal_height['id']: maternal_risk, '%s'%maternal_bmi['id']: maternal_nutrition, '%s'%maternal_anc['id']: anc3_reps, '%s'%birth_weight['id']: birth_w, '%s'%birth_term['id']: birth_t, '%s'%vaccination_dpt3['id']: vac_dpt3, '%s'%vaccination_measles['id']: vac_measles, '%s'%ebf1['id']: ebf1_reps, '%s'%ebf2['id']: ebf2_reps, '%s'%ebf3['id']: ebf3_reps, '%s'%ebf4['id']: ebf4_reps, '%s'%pnc1['id']: pnc1_reps, '%s'%pnc2['id']: pnc2_reps, '%s'%pnc3['id']: pnc3_reps, '%s'%anthro_h_6['id']: anthro_h_6_reps, '%s'%anthro_h_9['id']: anthro_h_9_reps, '%s'%anthro_h_18['id']: anthro_h_18_reps, '%s'%anthro_h_24['id']: anthro_h_24_reps, '%s'%anthro_w_6['id']: anthro_w_6_reps, '%s'%anthro_w_9['id']: anthro_w_9_reps, '%s'%anthro_w_18['id']: anthro_w_18_reps, '%s'%anthro_w_24['id']: anthro_w_24_reps, '%s'%unwe_6['id']: unwe_6_reps, '%s'%unwe_9['id']: unwe_9_reps, '%s'%unwe_18['id']: unwe_18_reps, '%s'%unwe_24['id']: unwe_24_reps, '%s'%stunted_6['id']: stunted_6_reps, '%s'%stunted_9['id']: stunted_9_reps, '%s'%stunted_18['id']: stunted_18_reps, '%s'%stunted_24['id']: stunted_24_reps, '%s'%wasted_6['id']: wasted_6_reps, '%s'%wasted_9['id']: wasted_9_reps, '%s'%wasted_18['id']: wasted_18_reps, '%s'%wasted_24['id']: wasted_24_reps }}
    #fields = Field.objects.filter( type__category__name = "Risk", **rez)
    return indics#maternal_risk.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description')

def get_my_child(report):
    birth = Report.objects.filter( patient = report.patient, type__name = 'Birth', date = report.date )
    if not birth.exists():  return None
    sex = 'Male'
    if birth[0].get_sex(): sex = birth[0].get_sex().type.description 
    valid_gender = helpers.get_good_sex( sex )
    valid_date = helpers.date_to_age_in_months(birth[0].date)
    weight = height = None
    try:
        weight = report.fields.filter(type__key = 'child_weight')[0].value
        height = report.fields.filter(type__key = 'child_height')[0].value
    except: pass
    return {'weight': weight, 'valid_age': valid_date, 'valid_gender': valid_gender, 'height': height}

def get_my_child_zscores(child):
    cg = childgrowth(adjust_height_data=False, adjust_weight_scores=False)
    wfa = lhfa = wfl = None
    cg = childgrowth(adjust_height_data=False, adjust_weight_scores=False)
    if not child or type(child) != dict: return {'wfa': wfa, 'lhfa': lhfa, 'wfl': wfl}
    if child['weight'] and child['valid_age'] and child['valid_gender']: wfa = cg.zscore_for_measurement('wfa', child['weight'], child['valid_age'], child['valid_gender'])
    if child['height'] and child['valid_age'] and child['valid_gender']: lhfa = cg.zscore_for_measurement('lhfa', child['height'], child['valid_age'], child['valid_gender'])
    if child['weight'] and child['valid_age'] and child['valid_gender'] and child['height']: wfl = cg.zscore_for_measurement('lhfa', child['weight'], child['valid_age'], child['valid_gender'], child['height'])
    
    return {'wfa': wfa, 'lhfa': lhfa, 'wfl': wfl}
    


@permission_required('ubuzima.can_view')
def view_nutrition(req, indic, format = 'html'):
    resp=pull_req_with_filters(req)
    filters = resp['filters']
    rez = my_filters(req, filters)
    #indicator = FieldType.objects.get(id = indic) 
    #pts = Field.objects.filter( type = indicator, **rez)
    hindics = nutrition_indicators(req,resp['filters'])
    pts = hindics['desc'][indic]
    resp['hindics'] = paginated(req, hindics['desc'][indic], prefix = 'hind')
    heads   = ['Reporter', 'Location', 'Patient', 'Type', 'Date']
    resp['headers'] = heads
    resp['reports'] = paginated(req, pts, prefix = 'ind')
    end = resp['filters']['period']['end']
    start = resp['filters']['period']['start']
    annot = resp['annot_l']
    ans_l, ans_m,resp['track'] = {},{},{}
    if format == 'csv':
        rsp = HttpResponse(mimetype='text/csv')
        rsp['Content-Disposition'] = 'attachment; filename=%s.csv'%hindics['home'][int(indic)-1]['desc']['desc']

        # The data is hard-coded here, but you could load it from a database or
        # some other source.
        #csv_data = csv_data = (
        #('First row', 'Foo', 'Bar', 'Baz'),
        #('Second row', 'A', 'B', 'C', '"Testing"', "Here's a quote"),
    #)

     #   t = loader.get_template('ubuzima/export.txt')
      #  c = Context({
       #     'data': csv_data
        #})
        #response.write(t.render(c))
        #return response
        #rsp = HttpResponse()
        #rsp['Content-Type'] = 'text/csv; encoding=%s' % (getdefaultencoding(),)
        wrt = csv.writer(rsp, dialect = 'excel-tab')
        fc = []
        for x in pts:
            try:    fc.append([x.report.reporter.connection().identity, x.report.location, x.report.patient, x.report.type, x.report.created])
            except: continue
        
        wrt.writerows([heads]+fc)
        
        return rsp
    if pts.exists(): 
        pts_l = pts.values("report__"+annot.split(',')[0],"report__"+annot.split(',')[1]).annotate(number=Count('id')).order_by("report__"+annot.split(',')[0])

        ans_l = {'pts' : pts_l, 'tot':pts.values("report__"+annot.split(',')[0],"report__"+annot.split(',')[1]).annotate(number=Count('id')).order_by("report__"+annot.split(',')[0])}

        pts_m = pts.extra(select={'year': 'EXTRACT(year FROM creation)','month': 'EXTRACT(month FROM creation)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')

        ans_m = {'pts' : pts_m, 'tot': pts.extra(select={'year': 'EXTRACT(year FROM creation)','month': 'EXTRACT(month FROM creation)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')}

        resp['track'] = {'items_l':ans_l, 'items_m':ans_m, 'months' : months_between(start,end), 'indicator': hindics['home'][int(indic)-1], 'type':type(hindics['desc'][indic][0])}
    return render_to_response(req, ('ubuzima/nutrition.html'), resp)

@permission_required('ubuzima.can_view')
def nutrition(req):
    resp=pull_req_with_filters(req)
    hindics = nutrition_indicators(req,resp['filters'])
    resp['hindics'] = paginated(req, hindics['home'], prefix = 'hind')
    return render_to_response(req,
            "ubuzima/nutrition_dash.html", resp)
###END OF NUTRITION TABLES, CHARTS, MAP
#   TODO: Error-prone list should be done in raw SQL. Later.


def generate_spreadsheet(request):
    """
    Generates an Excel spreadsheet for review by a staff member.
    """
    election = Election.objects.latest()

    ballots = election.ballots.all()
    ballots = SortedDict([(b, b.candidates.all()) for b in ballots])
    # Flatten candidate list after converting QuerySets into lists
    candidates = sum(map(list, ballots.values()), [])
    votes = [(v, v.get_points_for_candidates(candidates))
             for v in election.votes.all()]
    response = render_to_response("spreadsheet.html", {
        'ballots': ballots.items(),
        'votes': votes,
    })
    filename = "election%s.xls" % (election.year_num)
    response['Content-Disposition'] = 'attachment; filename='+filename
    response['Content-Type'] = 'application/vnd.ms-excel; charset=utf-8'

    return response

##use generic view

class ReportListView(ListView):

    context_object_name = "report_list"
    queryset = Report.objects.all()
    template_name = "ubuzima/report_list.html"



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
    period = get_params(req)
    rez = get_filters(req, start_key = "creation__gte", end_key = "creation__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Field.objects.filter(type__key = "nd",report__type__name = 'Death',  report__date__range = (period['period']['start'], period['period']['end'] ), **rez)


##End of Death

##CCM
##Average weight and height of 2 years olds
def get_avg_weight_2years(req):
    period = get_params(req)
    rez = get_filters(req, start_key = "creation__gte", end_key = "creation__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    
    return Field.objects.filter(type__key = "child_weight",report__type__name = 'Child Health',  report__date__range = (period['period']['start'] - datetime.timedelta(days = 720), period['period']['end'] - datetime.timedelta(days = 720)), **rez)
    

def get_avg_height_2years(req):
    period = get_params(req)
    rez = get_filters(req, start_key = "creation__gte", end_key = "creation__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Field.objects.filter(type__key = "child_height",report__type__name = 'Child Health',  report__date__range = (period['period']['start'] - datetime.timedelta(days = 720), period['period']['end'] - datetime.timedelta(days = 720)), **rez)

##Average weight of child at 3rd PNC
def get_avg_weight_pnc3(req):
    period = get_params(req)
    rez = get_filters(req, start_key = "creation__gte", end_key = "creation__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Field.objects.filter(type__key = "pnc3",report__type__name = 'PNC',  report__date__range = (period['period']['start'] - datetime.timedelta(days = Report.DAYS_PNC3), period['period']['end'] - datetime.timedelta(days = Report.DAYS_PNC3)), **rez)

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
    period = get_params(req)
    rez = get_filters(req, start_key = "creation__gte", end_key = "creation__lte", loc_key = "location__id", dst_key = "district__id", prv_key = "province__id")
    return Field.objects.filter(type__key = "bsr",report__type__name = 'Risk',  report__date__range = (period['period']['start'], period['period']['end'] ), **rez)



##END OF CCM

###START NEW BORN TABLES, CHARTS, MAP
@permission_required('ubuzima.can_view')
def newborn_indicators(req, flts):
    rez = my_filters(req, flts)
    pst = my_report_filters(req, flts)
    locz = my_report_loc(req,flts)
    locz1 = my_field_loc(req,flts)

    resp=pull_req_with_filters(req)
    reports = matching_reports(req,resp['filters'])
    resp['reports']=reports

    start = resp['filters']['period']['start']    
    end = resp['filters']['period']['end']

    start_24 = start - timedelta(days = 1000-1)
    end_24 = end - timedelta(days = 720-1)


    total_bir_24_ago = Report.objects.filter(type = ReportType.objects.get(name = "Birth"), date__range = (start_24,end_24), **locz[0]).filter(**locz[1]).count()

    period = get_params(req)
    total_bir = Report.objects.filter(type = ReportType.objects.get(name = "Birth"), **pst).filter(**locz[1]).count()
    total_pnc3 = Field.objects.filter(type__key = "pnc3", report__type__name = 'PNC',  report__date__range = (period['period']['start'] - datetime.timedelta(days = Report.DAYS_PNC3), period['period']['end'] - datetime.timedelta(days = Report.DAYS_PNC3)), **rez).count()

    var_bsr=get_bsr(req).filter(**locz1[1])
    var_avg_weight_2years=get_avg_weight_2years(req).filter(**locz1[1])
    var_avg_height_2years=get_avg_height_2years(req).filter(**locz1[1])
    var_avg_weight_pnc3=get_avg_weight_pnc3(req).filter(**locz1[1])

    cal_avg_weight_2years =var_avg_weight_2years.values('value').annotate(number=Count('id'))
    cal_avg_height_2years =var_avg_height_2years.values('value').annotate(number=Count('id'))
    cal_avg_weight_pnc3 =var_avg_weight_pnc3.values('value').annotate(number=Count('id'))
    
    print cal_avg_weight_pnc3.count()

    aver_weight=Decimal('0.0')
    for i in cal_avg_weight_2years:
        aver_weight= aver_weight + i['value']

    global average_weight_2years
    if cal_avg_weight_2years.count() != 0: average_weight_2years=Decimal(aver_weight)/Decimal(cal_avg_weight_2years.count())
    else: average_weight_2years= 0 

    aver_height=Decimal('0.0')
    for i in cal_avg_height_2years:
        aver_height= aver_height + i['value']

    global average_height_2years
    if cal_avg_height_2years.count() != 0: average_height_2years=Decimal(aver_height)/Decimal(cal_avg_height_2years.count())
    else: average_height_2years= 0

    aver_weight_pnc3=Decimal('0.0')
    global average_weight_pnc3
    
    if cal_avg_weight_pnc3.count() >= 2:    
        for i in cal_avg_weight_pnc3:
            aver_weight_pnc3 = aver_weight_pnc3 + i['value']

    if cal_avg_weight_pnc3.count() != 0: 
        average_weight_pnc3=Decimal(aver_weight_pnc3)/Decimal(cal_avg_weight_pnc3.count())
        
        
    else: average_weight_pnc3= 0
       
 
    var_newborn_death=get_newborn_death(req).filter(**locz1[1])
    var_child_death=get_child_death(req).filter(**locz1[1])
    
    indics = {'home':[{'desc':birth_sick_referred, 'fs':  var_bsr.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered birth " % total_bir, 'patients': var_bsr},
{'desc':newborn_death, 'fs':  var_newborn_death.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered birth " % total_bir, 'patients': var_newborn_death},
{'desc':child_death , 'fs':  var_child_death .values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " over %d registered birth " % total_bir, 'patients': var_child_death },
{'desc':avg_weight_2years, 'fs': var_avg_weight_2years.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description') , 'deno': " children, average weight: %d kg" % average_weight_2years, 'patients': var_avg_weight_2years},\
{'desc':avg_height_2years, 'fs':  var_avg_height_2years.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " children, average height: %d m " % average_height_2years, 'patients': var_avg_height_2years},\
{'desc':avg_weight_pnc3, 'fs':  var_avg_weight_pnc3.values('type__id','type__description').annotate(tot=Count('id')).order_by('type__description'), 'deno': " children, average weight: %d kg " % average_weight_pnc3, 'patients': total_pnc3},\
],\
'desc': { '%s'%birth_sick_referred['id']: var_bsr,'%s'%newborn_death['id']: var_newborn_death, '%s'%child_death['id']: var_child_death,'%s'%avg_weight_2years['id']: var_avg_weight_2years,'%s'%avg_height_2years['id']: var_avg_height_2years,'%s'% avg_weight_pnc3['id']: var_avg_weight_pnc3}}

    return indics

@permission_required('ubuzima.can_view')
def newborn(req):
    resp=pull_req_with_filters(req)
    hindics =newborn_indicators(req,resp['filters'])
    resp['hindics'] = paginated(req, hindics['home'], prefix = 'hind')
    return render_to_response(req,
            "ubuzima/newborn_dash.html", resp)




@permission_required('ubuzima.can_view')
def view_newborn(req, indic, format = 'html'):
    resp=pull_req_with_filters(req)
    filters = resp['filters']
    rez = my_filters(req, filters)
    hindics = newborn_indicators(req,resp['filters'])
    pts = hindics['desc'][indic]
    resp['hindics'] = paginated(req, hindics['desc'][indic], prefix = 'hind')
    heads   = ['Reporter', 'Location', 'Patient', 'Type', 'Date']
    resp['headers'] = heads
    resp['reports'] = paginated(req, pts, prefix = 'ind')
    end = resp['filters']['period']['end']
    start = resp['filters']['period']['start']
    annot = resp['annot_l']
    ans_l, ans_m,resp['track'] = {},{},{}
    if format == 'csv':
        rsp = HttpResponse(mimetype='text/csv')
        rsp['Content-Disposition'] = 'attachment; filename=%s.csv'%hindics['home'][int(indic)-1]['desc']['desc']

        wrt = csv.writer(rsp, dialect = 'excel-tab')
        fc = []
        for x in pts:
            try:    fc.append([x.report.reporter.connection().identity, x.report.location, x.report.patient, x.report.type, x.report.created])
            except: continue
        
        wrt.writerows([heads]+fc)
        
        return rsp
    if pts.exists(): 
        pts_l = pts.values("report__"+annot.split(',')[0],"report__"+annot.split(',')[1]).annotate(number=Count('id')).order_by("report__"+annot.split(',')[0])

        ans_l = {'pts' : pts_l, 'tot':pts.values("report__"+annot.split(',')[0],"report__"+annot.split(',')[1]).annotate(number=Count('id')).order_by("report__"+annot.split(',')[0])}

        pts_m = pts.extra(select={'year': 'EXTRACT(year FROM creation)','month': 'EXTRACT(month FROM creation)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')

        ans_m = {'pts' : pts_m, 'tot': pts.extra(select={'year': 'EXTRACT(year FROM creation)','month': 'EXTRACT(month FROM creation)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')}

        resp['track'] = {'items_l':ans_l, 'items_m':ans_m, 'months' : months_between(start,end), 'indicator': hindics['home'][int(indic)-1], 'type':type(hindics['desc'][indic][0])}
    return render_to_response(req, ('ubuzima/newborn.html'), resp)
###END OF NEW BORN TABLES, CHARTS, MAP

##End of New views for new RapidSMS to track 1000 days
