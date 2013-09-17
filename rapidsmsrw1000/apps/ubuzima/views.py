#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import json
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
from rapidsmsrw1000.apps.chws.models import *
from rapidsmsrw1000.apps.chws.utils import *
from rapidsmsrw1000.apps.utils import *
from sys import getdefaultencoding
from rapidsmsrw1000.apps.ubuzima.models import *
from rapidsmsrw1000.apps.ubuzima.utils import *
from rapidsmsrw1000.apps.ubuzima.constants import *
from rapidsmsrw1000.apps.ubuzima.newborn_ind import *
from rapidsmsrw1000.apps.ubuzima.enum import *
from django.contrib.auth.models import *
##working with generic view
from django.views.generic import ListView
from pygrowup import helpers, Calculator
#from pygrowup import helpers
from decimal import *
from rapidsmsrw1000.apps.ubuzima.get_data import get_red_alert_data


### START OF HELPERS
@permission_required('ubuzima.can_view')
def paginated(req, data):
    req.base_template = "webapp/layout.html"
    paginator = Paginator(data, 20)

    try: page = int(req.GET.get("page", '1'))
    except ValueError: page = 1

    try:
        data = paginator.page(page)
    except (InvalidPage, EmptyPage):
        data = paginator.page(paginator.num_pages)

    return data

@permission_required('ubuzima.can_view')
def get_user_location(req):
    req.base_template = "webapp/layout.html"
    try:
        uloc = UserLocation.objects.get(user=req.user)
        return uloc
    except UserLocation.DoesNotExist,e:
        return render_to_response("ubuzima/404.html",{'error':e}, context_instance=RequestContext(req))

###END OF HELPERS



@permission_required('ubuzima.can_view')
@require_http_methods(["GET"])
def index(req,**flts):
    req.base_template = "webapp/layout.html"
    uloc = get_user_location(req)
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
        lxn = HealthCentre.objects.get(id = lox)
        lxn=lxn.name+' '+"Health Centre"+', '+lxn.district.name+' '+"District"+', '+lxn.province.name+' '
    if req.REQUEST.has_key('csv'):
        heads = ['ReportID','Date','Facility', 'District', 'Province','Type','Reporter','Patient', 'LMP', 'EDD', 'DOB', 'VisitDate',' ANCVisit','NBCVisit','PNCVisit','MotherWeight','MotherHeight','ChildWeight','ChildHeight','MUAC', 'ChilNumber','Gender', 'Gravidity','Parity', 'VaccinationReceived' , 'VaccinationCompletion','Breastfeeding', 'Intevention', 'Status','Toilet','Handwash' , 'Located','Symptoms']
        htp = HttpResponse()
        htp['Content-Type'] = 'text/csv; encoding=%s' % (getdefaultencoding(),)
        wrt = csv.writer(htp, dialect = 'excel-tab')
        seq=[]
        for r in reports:
            try:
                seq.append([r.id, r.created,r.location,r.type,r.reporter.national_id,r.patient.national_id, r.summary()])
            except Reporter.DoesNotExist:
                continue
        wrt.writerows([heads]+seq)
        return htp
    elif req.REQUEST.has_key('excel'):
        return reports_to_excel(reports.order_by("-id"))
    else:

        # TODO start date and end date
        red_alerts = json.dumps(get_red_alert_data())
        return render_to_response("ubuzima/index.html", {"reports": paginated(req, reports),'usrloc':UserLocation.objects.get(user=req.user),'start_date': date.strftime(filters['period']['start'], '%d.%m.%Y'),
            'end_date': date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,'locationname':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1], 'red_alerts': red_alerts,
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

    return render_to_response("ubuzima/patient.html", { "patient":    patient,
                                                        "reports":    paginated(req, reports),
                                                        "reminders":  reminders ,'postqn':(req.get_full_path().split('?', 2) + [''])[1]}, context_instance=RequestContext(req))

@permission_required('ubuzima.can_view')
@require_http_methods(["GET"])
def by_national_id(req, national_id):
    patient = get_object_or_404(Patient, national_id=national_id)
    reports = Report.objects.filter(patient=patient).order_by("-created")

    # look up any reminders sent to this patient
    reminders = []
    for report in reports:
        for reminder in report.reminders.all():
            reminders.append(reminder)

    return render_to_response("ubuzima/patient.html", { "patient":    patient,
                                                        "reports":    paginated(req, reports),
                                                        "reminders":  reminders ,'postqn':(req.get_full_path().split('?', 2) + [''])[1]}, context_instance=RequestContext(req))

@require_http_methods(["GET"])
@permission_required('ubuzima.can_view')
def by_type(req, pk, **flts):
    report_type = get_object_or_404(ReportType, pk=pk)
    filters = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    reports = matching_reports(req,filters).filter(type=report_type).order_by("-created")
    lox, lxn, title = 0, location_name(req), report_type
    
    if req.REQUEST.has_key('cat'):

        try:
            if req.REQUEST['cat'] == 'hrisk':
                reports = fetch_high_risky_preg(reports)
                title   = "High Risk Pregnant Women"

            elif req.REQUEST['cat'] == 'pre_w' or req.REQUEST['cat'] == 'edd_2_w' or req.REQUEST['cat'] == 'hedd_2_w':
                resp=pull_req_with_filters(req)
                end = resp['filters']['period']['end']
                start = resp['filters']['period']['start']
                annot = resp['annot_l']
                locs = resp['locs']
                rez = {}
                rez['%s__in'%annot.split(',')[1]] = [l.pk for l in locs]
                
                if req.REQUEST['cat'] == 'pre_w':
                    reports = Report.objects.filter(type__name = 'Pregnancy', edd_date__gte = end).filter(** rez)
                    title   = "Pregnant Women on %d/%d/%d" % (end.day, end.month, end.year)
                elif req.REQUEST['cat'] == 'edd_2_w':
                    title   = "Pregnant Women Expected to deliver next two weeks from %d/%d/%d" % (end.day, end.month, end.year)
                    reports = Report.objects.filter(type__name = 'Pregnancy', edd_date__gte = end , \
                                                                                edd_date__lte = end + timedelta(days = 14)).filter(** rez)
                elif req.REQUEST['cat'] == 'hedd_2_w':
                    title   = "High Risk Pregnant Women Expected to deliver next two weeks from %d/%d/%d" % (end.day, end.month, end.year)
                    reports = fetch_high_risky_preg(Report.objects.filter(type__name = 'Pregnancy', edd_date__gte = end , \
                                                                                edd_date__lte = end + timedelta(days = 14)).filter(** rez))   
            elif req.REQUEST['cat'] == 'edd':
                resp=pull_req_with_filters(req)
                end = resp['filters']['period']['end']
                start = resp['filters']['period']['start']
                annot = resp['annot_l']
                locs = resp['locs']
                rez = {}
                rez['%s__in'%annot.split(',')[1]] = [l.pk for l in locs]
                
                reports = fetch_edd( start, end).filter(** rez)
                title   = "Pregnant Women Expected to deliver from %d/%d/%d to %d/%d/%d" % (start.day, start.month, start.year,end.day, end.month, end.year)

            elif req.REQUEST['cat'] == 'hedd':
                resp=pull_req_with_filters(req)
                end = resp['filters']['period']['end']
                start = resp['filters']['period']['start']
                annot = resp['annot_l']
                locs = resp['locs']
                rez = {}
                rez['%s__in'%annot.split(',')[1]] = [l.pk for l in locs]
                
                reports = fetch_high_risky_preg(fetch_edd( start, end).filter(** rez))
                title   = "High Risk Pregnant Women Expected to deliver from %d/%d/%d to %d/%d/%d" % (start.day, start.month, start.year,end.day, end.month, end.year)
        except Exception, e: pass

    if req.REQUEST.has_key('location') and req.REQUEST['location'] != '0':
        lox = int(req.REQUEST['location'])
        lxn = HealthCentre.objects.get(id = lox)
        lxn=lxn.name+' '+"Health Centre"+', '+lxn.district.name+' '+"District"+', '+lxn.province.name+' '

    if req.REQUEST.has_key('csv'):
        heads = ['ReportID','Date','Facility', 'District', 'Province','Type','Reporter','Patient', 'LMP', 'DOB', 'VisitDate',' ANCVisit','NBCVisit','PNCVisit','MotherWeight','MotherHeight','ChildWeight','ChildHeight','MUAC', 'ChilNumber','Gender', 'Gravidity','Parity', 'VaccinationReceived' , 'VaccinationCompletion','Breastfeeding', 'Intevention', 'Status','Toilet','Handwash' , 'Located','Symptoms']
        htp = HttpResponse()
        htp['Content-Type'] = 'text/csv; encoding=%s' % (getdefaultencoding(),)
        wrt = csv.writer(htp, dialect = 'excel-tab')
        seq=[]
        for r in reports:
            try:
                seq.append([r.id, r.created,r.location,r.type,r.reporter.national_id,r.patient.national_id, r.summary()])
            except Reporter.DoesNotExist:
                continue
        wrt.writerows([heads]+seq)
        return htp
    elif req.REQUEST.has_key('excel'):
        return reports_to_excel(reports.order_by("-id"))
    else:
        return render_to_response("ubuzima/type.html", { 'title': title, "type":    report_type,
                                                     "reports":    paginated(req, reports),'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),
         'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,'locationname':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1] }, context_instance=RequestContext(req))


@require_http_methods(["GET"])
@permission_required('ubuzima.can_view')
def view_report(req, pk):
    report = get_object_or_404(Report, pk=pk)
    req.base_template = "webapp/layout.html"
    return render_to_response("ubuzima/report.html", { "report":    report ,'postqn':(req.get_full_path().split('?', 2) + [''])[1]}, context_instance=RequestContext(req))


@require_http_methods(["GET"])
@permission_required('ubuzima.can_view')
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
        lxn = HealthCentre.objects.get(id = lox)
        lxn=lxn.name+' '+"Health Centre"+', '+lxn.district.name+' '+"District"+', '+lxn.province.name+' '
    return render_to_response("ubuzima/reporter.html", { "reports":    paginated(req, reports),
                                                         "reporter":   reporter,'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),
         'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,'locationname':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1] }, context_instance=RequestContext(req))

@permission_required('ubuzima.can_view')
@require_http_methods(["GET"])
def by_location(req, pk, **flts):
    location = get_object_or_404(HealthCentre, pk=pk)
    filters = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    reports = matching_reports(req,filters).filter(location = location).order_by("-created")
    lox, lxn = 0, location_name(req)
    if req.REQUEST.has_key('location') and req.REQUEST['location'] != '0':
        lox = int(req.REQUEST['location'])
        lxn = HealthCentre.objects.get(id = lox)
        lxn=lxn.name+' '+"Health Centre"+', '+lxn.district.name+' '+"District"+', '+lxn.province.name+' '

    return render_to_response("ubuzima/location.html", { "location":   location,
                                                         "reports":   paginated(req, reports),'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),
         'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,'locationname':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1] }, context_instance=RequestContext(req))




def child_locs(loc,filters):
    #print filters['province'], filters['district'], filters['location']
    if type(loc) == Nation: return Province.objects.filter(nation = loc)
    elif type(loc) == Province: return filters['district'] if filters['district'] else HealthCentre.objects.filter(province = loc).order_by('name')
    elif type(loc) == District: return filters['location'] if filters['location'] else HealthCentre.objects.filter(district = loc).order_by('name')
    elif type(loc) == HealthCentre: return filters['location'] if filters['location'] else HealthCentre.objects.filter(id = loc.id).order_by('name')

@permission_required('ubuzima.can_view')
def pull_req_with_filters(req):
    try:
        p = get_user_location(req)
        sel,prv,dst,lxn=None,None,None,None
        filters = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req),}
        try:    sel,lxn=HealthCentre.objects.get(pk=int(req.REQUEST['location'])),HealthCentre.objects.get(pk=int(req.REQUEST['location']))
        except KeyError:
            try:    sel,dst=District.objects.get(pk=int(req.REQUEST['district'])),District.objects.get(pk=int(req.REQUEST['district']))
            except KeyError:
                try:    sel,prv=Province.objects.get(pk=int(req.REQUEST['province'])),Province.objects.get(pk=int(req.REQUEST['province']))
                except KeyError:    pass
        #print type(sel), dst, prv
        if not sel: sel = p.health_centre or p.district or p.province or p.nation
        locs = child_locs(sel,filters)
        if p.nation:    locs = locs.filter(nation = p.nation)
        if p.province:  locs = locs.filter(province = p.province)
        if p.district:  locs = locs.filter(district = p.district)
        if p.health_centre: locs = locs.filter(id = p.health_centre.id)


        #print locs
        return {'usrloc':UserLocation.objects.get(user=req.user),'locs':locs,'annot':annot_val(sel),'annot_l':annot_locs_val(sel),'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),
             'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,'sel':sel,'prv':prv,'dst':dst,'lxn':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1]}
    except UserLocation.DoesNotExist,e:
        return render_to_response("404.html",{'error':e}, context_instance=RequestContext(req))

def annot_val(loc):
    if type(loc) == Nation: return "nation__name,nation__pk"
    elif type(loc) == Province: return "province__name,province__pk"
    elif type(loc) == District: return "district__name,district__pk"
    else: return "location__name,location__pk"

def annot_locs_val(loc):
    if type(loc) == Nation: return "province__name,province__pk"
    elif type(loc) == Province: return "district__name,district__pk"
    elif type(loc) == District: return "location__name,location__pk"
    else: return "location__name,location__pk"


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

def fetch_edd_info(qryset, start, end):
    edd_start,edd_end=Report.calculate_last_menses(start),Report.calculate_last_menses(end)
    dem  = Report.objects.filter(type = ReportType.objects.get(name = 'Pregnancy'), date__gte =
            edd_start, date__lte = edd_end,location__in=qryset.values('location')).select_related('patient')
    return dem
def fetch_edd(start, end):
    #edd_start,edd_end=Report.calculate_last_menses(start),Report.calculate_last_menses(end)
    #dem  = Report.objects.filter(type = ReportType.objects.get(name = 'Pregnancy'), date__gte =
            #edd_start, date__lte = edd_end).select_related('patient')
    dem  = Report.objects.filter(type = ReportType.objects.get(name = 'Pregnancy'), edd_date__gte =start, edd_date__lte = end).select_related('patient')
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
    return qryset.filter(fields__in=Field.objects.filter(type__in = FieldType.objects.filter(category=FieldCategory.objects.get(name='Vaccination Codes')))).distinct()

def fetch_vaccinated_stats(reps):
    track={}
    for r in FieldType.objects.filter(category=FieldCategory.objects.get(name='Vaccination Codes')): track[r.key]=reps.filter(fields__in = Field.objects.filter(type=FieldType.objects.get(key=r.key))).distinct()
    return track

def fetch_high_risky_preg(qryset):    
    return qryset.filter(fields__type__key__in = ['gs','rm','ol','yg','mu']).distinct()

def fetch_without_toilet(qryset):
    return qryset.filter(fields__in = Field.objects.filter(type = FieldType.objects.get(key ='nt')))

def fetch_without_hw(qryset):
    return qryset.filter(fields__in = Field.objects.filter(type = FieldType.objects.get(key ='nh')))

@permission_required('ubuzima.can_view')
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

###START OF FLASH REPORT

@permission_required('ubuzima.can_view')
def flash_report(req):
    
    resp=pull_req_with_filters(req)
    resp['reports']=matching_reports(req,resp['filters'])
    end = resp['filters']['period']['end']
    start = resp['filters']['period']['start']
    preg = resp['reports'].filter(type__name = 'Pregnancy')
    pregnant_women = Report.objects.filter( type__name = 'Pregnancy' , edd_date__gte = end )
    annot = resp['annot_l']
    locs = resp['locs']
    ans_l, ans_m, rez = {}, {}, {}
    rez['%s__in'%annot.split(',')[1]] = [l.pk for l in locs]
    edd = fetch_edd( start, end).filter(** rez)
    resp['reports'] = paginated(req, preg)
    if preg.exists() or edd.exists(): 
        preg_l, preg_risk_l, edd_l, edd_risk_l, pre_w, edd_2_w = preg.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), fetch_high_risky_preg(preg).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), edd.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), fetch_high_risky_preg(edd).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]) ,pregnant_women.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), pregnant_women.filter(edd_date__gte = end , edd_date__lte = end + timedelta(days = 14)).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])
        
        hedd_2_w = fetch_high_risky_preg(edd_2_w).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])
    
        ans_l = {'pre' : preg_l, 'prehr' : preg_risk_l, 'edd': edd_l, 'eddhr': edd_risk_l, 'pre_w' : pre_w, 'edd_2_w' : edd_2_w, 'hedd_2_w' : hedd_2_w}
        
        preg_m, preg_risk_m, edd_m, edd_risk_m = preg.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), fetch_high_risky_preg(preg).extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), edd.extra(select={'year': 'EXTRACT(year FROM edd_date)','month': 'EXTRACT(month FROM edd_date)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'),fetch_high_risky_preg(edd).extra(select={'year': 'EXTRACT(year FROM edd_date)','month': 'EXTRACT(month FROM edd_date)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')

        ans_m = {'pre' : preg_m, 'prehr' : preg_risk_m, 'edd': edd_m, 'eddhr': edd_risk_m}
        
    resp['track'] = {'items_l':ans_l, 'items_m':ans_m, 'months' : months_between(start,end), 'months_edd' : months_between(start,end)}
    resp['report_type'] = ReportType.objects.get(name = 'Pregnancy')
    if req.REQUEST.has_key('csv') or req.REQUEST.has_key('excel'):  return reports_to_excel(resp['reports'])  
    else:   return render_to_response('ubuzima/flash_report.html',
           resp, context_instance=RequestContext(req))
##END OF FLASH REPORT


##START OF PREGNANCY TABLES, CHARTS, MAP
@permission_required('ubuzima.can_view')
def preg_report(req):
    
    resp=pull_req_with_filters(req)
    resp['reports']=matching_reports(req,resp['filters'])
    end = resp['filters']['period']['end']
    start = resp['filters']['period']['start']
    preg = resp['reports'].filter(type__name = 'Pregnancy')
    pregnant_women = Report.objects.filter( type__name = 'Pregnancy' , edd_date__gte = end )
    annot = resp['annot_l']
    locs = resp['locs']
    ans_l, ans_m, rez = {}, {}, {}
    rez['%s__in'%annot.split(',')[1]] = [l.pk for l in locs]
    edd = fetch_edd( start, end).filter(** rez)
    resp['reports'] = paginated(req, preg)
    if preg.exists() or edd.exists(): 
        preg_l, preg_risk_l, edd_l, edd_risk_l, pre_w, edd_2_w = preg.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), fetch_high_risky_preg(preg).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), edd.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), fetch_high_risky_preg(edd).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]) ,pregnant_women.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), pregnant_women.filter(edd_date__gte = end , edd_date__lte = end + timedelta(days = 14)).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])
        
        hedd_2_w = fetch_high_risky_preg(edd_2_w).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])
    
        ans_l = {'pre' : preg_l, 'prehr' : preg_risk_l, 'edd': edd_l, 'eddhr': edd_risk_l, 'pre_w' : pre_w, 'edd_2_w' : edd_2_w, 'hedd_2_w' : hedd_2_w}
        
        preg_m, preg_risk_m, edd_m, edd_risk_m = preg.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), fetch_high_risky_preg(preg).extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), edd.extra(select={'year': 'EXTRACT(year FROM edd_date)','month': 'EXTRACT(month FROM edd_date)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'),fetch_high_risky_preg(edd).extra(select={'year': 'EXTRACT(year FROM edd_date)','month': 'EXTRACT(month FROM edd_date)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')

        ans_m = {'pre' : preg_m, 'prehr' : preg_risk_m, 'edd': edd_m, 'eddhr': edd_risk_m}
        
    resp['track'] = {'items_l':ans_l, 'items_m':ans_m, 'months' : months_between(start,end), 'months_edd' : months_between(start,end)}
    resp['report_type'] = ReportType.objects.get(name = 'Pregnancy')
    if req.REQUEST.has_key('csv') or req.REQUEST.has_key('excel'):  return reports_to_excel(preg)  
    else:   return render_to_response('ubuzima/preg_report.html',
           resp, context_instance=RequestContext(req))
##END OF PREGNANCY TABLES, CHARTS, MAP

###START PNC TABLES, CHARTS, MAP
def fetch_pnc1_info(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'pnc1'))).distinct()

def fetch_pnc2_info(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'pnc2'))).distinct()

def fetch_pnc3_info(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'pnc3'))).distinct()

@permission_required('ubuzima.can_view')
def pnc_report(req):
    resp=pull_req_with_filters(req)
    resp['reports']=matching_reports(req,resp['filters'])
    qryset = resp['reports'].filter(type__name = 'PNC', fields__in = Field.objects.filter(type__key__in = ["pnc1","pnc2","pnc3"]))
    end = resp['filters']['period']['end']
    start = resp['filters']['period']['start']
    annot=resp['annot_l']
    locs=resp['locs']
    ans_l, ans_m = {},{}
    resp['reports'] = paginated(req, qryset)
    if qryset.exists():
        pnc1_m,pnc2_m,pnc3_m = fetch_pnc1_info(qryset),fetch_pnc2_info(qryset),fetch_pnc3_info(qryset)

        pnc1_c, pnc2_c, pnc3_c = pnc1_m.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), pnc2_m.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), pnc3_m.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')

        ans_m = {'pnc1_m' : pnc1_c, 'pnc2_m' : pnc2_c, 'pnc3_m': pnc3_c ,'tot_m': qryset.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')}



        pnc1_l= fetch_pnc1_info(qryset).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])

        pnc2_l= fetch_pnc2_info(qryset).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])
        pnc3_l= fetch_pnc3_info(qryset).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])

        ans_l = {'pnc1' : pnc1_l, 'pnc2' : pnc2_l, 'pnc3': pnc3_l, 'tot':qryset.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])}


    resp['track'] = {'items':ans_l, 'items_m':ans_m, 'months' : months_between(start,end)}

    if req.REQUEST.has_key('csv') or req.REQUEST.has_key('excel'):  return reports_to_excel(qryset)  
    else:   return render_to_response('ubuzima/pnc_report.html',
           resp, context_instance=RequestContext(req))

###END OF PNC TABLES, CHARTS, MAP


###START NEWBORN TABLES, CHARTS, MAP
def fetch_nbc1_info(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'nbc1'))).distinct()

def fetch_nbc2_info(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'nbc2'))).distinct()

def fetch_nbc3_info(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'nbc3'))).distinct()

def fetch_nbc4_info(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'nbc4'))).distinct()

def fetch_nbc5_info(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'nbc5'))).distinct()

@permission_required('ubuzima.can_view')
def newborn_report(req):
    resp=pull_req_with_filters(req)
    resp['reports']=matching_reports(req,resp['filters'])
    qryset = resp['reports'].filter(type__name = 'Newborn Care', fields__in = Field.objects.filter(type__key__in = ["nbc1","nbc2","nbc3","nbc4","nbc5"]))
    end = resp['filters']['period']['end']
    start = resp['filters']['period']['start']
    annot=resp['annot_l']
    locs=resp['locs']
    ans_l, ans_m = {},{}
    resp['reports'] = paginated(req, qryset)
    if qryset.exists():
        nbc1_m,nbc2_m,nbc3_m = fetch_nbc1_info(qryset),fetch_nbc2_info(qryset),fetch_nbc3_info(qryset)

        nbc1_c, nbc2_c, nbc3_c = nbc1_m.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), nbc2_m.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), nbc3_m.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')

        ans_m = {'nbc1_m' : nbc1_c, 'nbc2_m' : nbc2_c, 'nbc3_m': nbc3_c ,'tot_m': qryset.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')}



        nbc1_l= fetch_nbc1_info(qryset).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])

        nbc2_l= fetch_nbc2_info(qryset).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])
        nbc3_l= fetch_nbc3_info(qryset).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])

        ans_l = {'nbc1' : nbc1_l, 'nbc2' : nbc2_l, 'nbc3': nbc3_l, 'tot':qryset.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])}


    resp['track'] = {'items':ans_l, 'items_m':ans_m, 'months' : months_between(start,end)}#; print resp['track']
    if req.REQUEST.has_key('csv') or req.REQUEST.has_key('excel'):  return reports_to_excel(qryset)  
    else:   return render_to_response('ubuzima/newborn_report.html',
           resp, context_instance=RequestContext(req))
###END OF NEWBORN TABLES, CHARTS, MAP


###START CCM TABLES, CHARTS, MAP

def fetch_diarrhea_info(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'di'))).distinct()

def fetch_malaria_info(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'ma'))).distinct()

def fetch_pneumonia_info(qryset):
    return qryset.filter(fields__in=Field.objects.filter(type=FieldType.objects.get(key = 'pc'))).distinct()


@permission_required('ubuzima.can_view')
def community_report(req):
    resp=pull_req_with_filters(req)
    resp['reports']=matching_reports(req,resp['filters'])
    qryset = resp['reports'].filter(type__name = 'Community Case Management', fields__in = Field.objects.filter(type__key__in = ["di","ma","pc"]))
    end = resp['filters']['period']['end']
    start = resp['filters']['period']['start']
    annot=resp['annot_l']
    locs=resp['locs']
    ans_l, ans_m = {},{}
    resp['reports'] = paginated(req, qryset)
    if qryset.exists():
        diarrhea_m,malaria_m,pneumonia_m = fetch_diarrhea_info(qryset),fetch_malaria_info(qryset),fetch_pneumonia_info(qryset)

        diarrhea_c, malaria_c, pneumonia_c = diarrhea_m.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), malaria_m.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), pneumonia_m.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')

        ans_m = {'diarrhea_m' : diarrhea_c, 'malaria_m' : malaria_c, 'pneumonia_m': pneumonia_c ,'tot_m': qryset.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')}



        diarrhea_l= fetch_diarrhea_info(qryset).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])

        malaria_l= fetch_malaria_info(qryset).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])
        pneumonia_l= fetch_pneumonia_info(qryset).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])

        ans_l = {'diarrhea' : diarrhea_l, 'malaria' : malaria_l, 'pneumonia': pneumonia_l, 'tot':qryset.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])}


    resp['track'] = {'items':ans_l, 'items_m':ans_m, 'months' : months_between(start,end)}
    if req.REQUEST.has_key('csv') or req.REQUEST.has_key('excel'):  return reports_to_excel(qryset)  
    else:   return render_to_response('ubuzima/community_report.html',
           resp, context_instance=RequestContext(req))

###END OF CCM TABLES, CHARTS, MAP




#Reminders Logs! Ceci interroger la base de donnees et presenter a la page nommee remlog.html, toutes les rappels envoyes par le systeme!
@permission_required('ubuzima.can_view')
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

@permission_required('ubuzima.can_view')
def match_filters_fresher(req):
    pst={}
    try:
        level = get_level(req)
        if level['level'] == 'Nation':  pst['nation__id'] = level['uloc'].nation.id
        elif level['level'] == 'Province':  pst['province__id'] = level['uloc'].province.id
        elif level['level'] == 'District':  pst['district__id'] = level['uloc'].district.id
        elif level['level'] == 'HealthCentre':  pst['location__id'] = level['uloc'].health_centre.id

    except UserLocation.DoesNotExist:
        pass
    return pst


@permission_required('ubuzima.can_view')
def view_reminders(req, **flts):
    filters = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    lox, lxn = 0, location_name(req)
    if req.REQUEST.has_key('location') and req.REQUEST['location'] != '0':
        lox = int(req.REQUEST['location'])
        lxn = HealthCentre.objects.get(id = lox)
        lxn=lxn.name+', '+lxn.district.name+', '+lxn.province.name
    template_name="ubuzima/remlog.html"
    req.base_template = "webapp/layout.html"
    rez=match_filters(req,filters)
    pst=match_filters_fresher(req)
    remlogs=Reminder.objects.filter(**rez).order_by('-date')

    rems_by_type = []#remlogs.values('type__name','type__pk').annotate(number = Count('id')).order_by('type__name')
    rem_types = ReminderType.objects.all().order_by('id')
    #for rem in rem_types:   print rem.id, rem.name, remlogs.filter(type = rem).count()
    for rem in rem_types:
        rems_by_type.append({ 'type': rem , 'number': remlogs.filter(type = rem).count() })

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
        reminders = remlogs.filter(**pst)
        print rez, pst
        return render_to_response(template_name, { "reminders": paginated(req, reminders), 'remts': rems_by_type,'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),'usrloc':UserLocation.objects.get(user=req.user),
             'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,'locationname':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1]}, context_instance=RequestContext(req))


@permission_required('ubuzima.can_view')
def view_delivery_nots(req, **flts):
    filters = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    lox, lxn = 0, location_name(req)
    if req.REQUEST.has_key('location') and req.REQUEST['location'] != '0':
        lox = int(req.REQUEST['location'])
        lxn = HealthCentre.objects.get(id = lox)
        lxn=lxn.name+' , '+lxn.district.name+' , '+lxn.province.name
    template_name="ubuzima/remlog.html"
    req.base_template = "webapp/layout.html"
    rez=match_filters(req,filters)
    pst=match_filters_fresher(req)
    remlogs=Reminder.objects.filter(**rez).order_by('-date')

    rems_by_type = []#remlogs.values('type__name','type__pk').annotate(number = Count('id')).order_by('type__name')
    rem_types = ReminderType.objects.filter(name__in = ['Two Weeks Before Expected Delivery Date', 'Week Before Expected Delivery Date', 'Due Date', 'Week After Due Date']).order_by('id')
    for rem in rem_types:   print rem.id, rem.name, remlogs.filter(type = rem).count()
    for rem in rem_types:
        rems_by_type.append({ 'type': rem , 'number': remlogs.filter(type = rem).count() })

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
        reminders = remlogs.filter(**pst)

        return render_to_response(template_name, { "reminders": paginated(req, reminders), 'remts': rems_by_type,'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),'usrloc':UserLocation.objects.get(user=req.user),
             'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,'locationname':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1]}, context_instance=RequestContext(req))

@permission_required('ubuzima.can_view')
def remlog_by_type(req,pk,**flts):
    filters = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    lox, lxn = 0, location_name(req)
    if req.REQUEST.has_key('location') and req.REQUEST['location'] != '0':
        lox = int(req.REQUEST['location'])
        lxn = HealthCentre.objects.get(id = lox)
        lxn=lxn.name+' , '+lxn.district.name+' , '+lxn.province.name
    template_name="ubuzima/remlog.html"
    rem_type=ReminderType.objects.get(pk=pk)
    rez=match_filters(req,filters)
    remlogs=Reminder.objects.filter(type=rem_type,**rez).order_by('-date')
    rems_by_type = [{ 'type' : rem_type, 'number' : remlogs.filter(type = rem_type).count() }]#remlogs.values('type__name','type__pk').annotate(number = Count('id')).order_by('type__name')
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
        return render_to_response(template_name, { "reminders": paginated(req, remlogs),'remts': rems_by_type,'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),'usrloc':UserLocation.objects.get(user=req.user),
         'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,'locationname':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1]}, context_instance=RequestContext(req))
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
        lxn = HealthCentre.objects.get(id = lox)
        lxn=lxn.name+' , '+lxn.district.name+' , '+lxn.province.name
    template_name="ubuzima/alertlog.html"
    rez=match_filters(req,filters)
    pst=match_filters_fresher(req)
    alertlogs=TriggeredAlert.objects.filter(**rez).order_by('-date')
    triggers = [] #alertlogs.values('trigger__name','trigger__pk').annotate(number = Count('id')).order_by('trigger__name')
    trigger_type = TriggeredText.objects.all().order_by('name')
    for trigger in trigger_type:
        triggers.append({ 'type': trigger, 'number' : alertlogs.filter(trigger = trigger).count() })

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
        return render_to_response(template_name, { "alerts": paginated(req, alertlogs.filter(**pst)),'triggers': triggers,'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),'usrloc':UserLocation.objects.get(user=req.user),
             'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,'locationname':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1]}, context_instance=RequestContext(req))

@permission_required('ubuzima.can_view')
def alerts_by_type(req,pk,**flts):
    filters = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    lox, lxn = 0, location_name(req)
    if req.REQUEST.has_key('location') and req.REQUEST['location'] != '0':
        lox = int(req.REQUEST['location'])
        lxn = HealthCentre.objects.get(id = lox)
        lxn=lxn.name+' , '+lxn.district.name+' , '+lxn.province.name
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
        return render_to_response(template_name, { "alerts": paginated(req, alertlogs.filter(**pst)),'triggers': triggers,'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),'usrloc':UserLocation.objects.get(user=req.user),
             'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,'locationname':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1]}, context_instance=RequestContext(req))

#End of Alerts logs




### IBIBARI DASHBOARD

@permission_required('ubuzima.can_view')
def view_indicator(req, indic, format = 'html'):
    resp=pull_req_with_filters(req)
    filters = resp['filters']
    rez = my_filters(req, filters)
    indicator = FieldType.objects.get(id = indic)
    pts = Field.objects.filter( type = indicator, **rez)
    heads   = ['Reporter', 'Location', 'Patient', 'Type', 'Date']
    resp['headers'] = heads
    resp['reports'] = paginated(req, pts)
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
    return render_to_response('ubuzima/indicator.html', resp, context_instance=RequestContext(req))

@permission_required('ubuzima.can_view')
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

@permission_required('ubuzima.can_view')
def ibibari_indicators(req, flts):
    rez = my_filters(req, flts)
    field_types = FieldType.objects.filter( key__in = ['ib'])
    fields = Field.objects.filter( type__in = field_types, **rez).order_by('type__description')
    stats = []
    for ft in field_types:
        stats.append({'type' : ft , 'total' : fields.filter(type = ft).count()})
    #print stats
    return stats

@permission_required('ubuzima.can_view')
def ibibari(req):
    resp=pull_req_with_filters(req)
    hindics = ibibari_indicators(req,resp['filters'])
    print hindics
    resp['hindics'] = paginated(req, hindics)
    return render_to_response(
            "ubuzima/ibibari.html", resp, context_instance=RequestContext(req))




###START ANC TABLES, CHARTS, MAP
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

@permission_required('ubuzima.can_view')
def anc_report(req):
    resp=pull_req_with_filters(req)
    reports = matching_reports(req,resp['filters'])
    resp['reports']=reports
    end = resp['filters']['period']['end']
    start = resp['filters']['period']['start']

    qryset=resp['reports'].filter(type__name__in =['ANC','Pregnancy'])
    ##qryset = resp['reports'].filter(fields__in = Field.objects.filter(type__key__in = ["anc2","anc3","anc4"]))
    preg_reps=resp['reports'].filter(type__name='Pregnancy',created__gte = start, created__lte = end)

    annot=resp['annot_l']
    locs=resp['locs']
    ans_l, ans_m = {},{}
    

    #new_qryset=resp['reports'].filter(type__name= 'Pregnancy',date__gte = start , date__lte = end )

    resp['reports'] = paginated(req, qryset)



    if qryset.exists():


        anc1_c = preg_reps.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')

        anc2_c = fetch_anc2_info(qryset).extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')
        anc3_c = fetch_anc3_info(qryset).extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')
        anc4_c = fetch_anc4_info(qryset).extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')
        #eddanc2_c = fetch_eddanc2_info(qryset,start,end).extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')
        #eddanc3_c = fetch_eddanc3_info(qryset,start,end).extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')
        #eddanc4_c = fetch_eddanc4_info(qryset,start,end).extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')


        #ans_m = {'anc1_m' : anc1_c, 'anc2_m' : anc2_c, 'anc3_m': anc3_c, 'anc4_m': anc4_c, 'eddanc2_m': eddanc2_c, 'eddanc3_m': eddanc3_c, 'eddanc4_m': eddanc4_c,'tot_m': qryset.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')}


        ans_m = {'anc1_m' : anc1_c, 'anc2_m' : anc2_c, 'anc3_m': anc3_c, 'anc4_m': anc4_c,'tot_m': qryset.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')}

        print anc1_c

        anc1_l=preg_reps.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])
        anc2_l=fetch_anc2_info(qryset).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])
        anc3_l=fetch_anc3_info(qryset).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])
        anc4_l=fetch_anc4_info(qryset).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])
        #eddanc2_l=fetch_eddanc2_info(qryset,start,end).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])
        #eddanc3_l=fetch_eddanc3_info(qryset,start,end).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])
        #eddanc4_l = fetch_eddanc4_info(qryset,start,end).values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])

        #ans_l = {'anc1' : anc1_l, 'anc2' : anc2_l, 'anc3': anc3_l, 'anc4': anc4_l, 'eddanc2': eddanc2_l, 'eddanc3': eddanc3_l, 'eddanc4': eddanc4_l, 'tot':qryset.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])}

        ans_l = {'anc1' : anc1_l, 'anc2' : anc2_l, 'anc3': anc3_l, 'anc4': anc4_l, 'tot':qryset.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])}


    resp['track'] = {'items':ans_l, 'items_m':ans_m, 'months' : months_between(start,end)}
    if req.REQUEST.has_key('csv') or req.REQUEST.has_key('excel'):  return reports_to_excel(qryset)  
    else:   return render_to_response('ubuzima/anc_report.html',
           resp, context_instance=RequestContext(req))

###END OF ANC TABLES, CHARTS, MAP

##START OF BIRTH TABLES, CHARTS, MAP
@permission_required('ubuzima.can_view')
def birth_report(req):
    resp=pull_req_with_filters(req)
    resp['reports']=matching_reports(req,resp['filters'])
    end = resp['filters']['period']['end']
    start = resp['filters']['period']['start']
    #qryset = resp['reports'].filter(type__name='Birth')
    qryset = resp['reports'].filter(type__name='Birth', date__gte = start, date__lte = end )#resp['reports'].filter(type__name='Birth', created__gte = start, created__lte = end )
    #print qryset.count()
    annot=resp['annot_l']
    locs=resp['locs']
    #print qryset.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])
    ans_l, ans_m = {}, {}
    resp['reports'] = paginated(req, qryset)
    if qryset.exists():
        fac,route,home = fetch_hosp_deliveries(qryset),fetch_en_route_deliveries(qryset),fetch_home_deliveries(qryset)
        #unk = qryset.exclude(id__in = fac).exclude(id__in = route).exclude(id__in = home)
        #qryset = qryset.exclude(id__in = unk)
        #resp['reports'] = paginated(req, qryset)

        home_l,fac_l,route_l = home.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), fac.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), route.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])

        ans_l = {'fac' : fac_l, 'route' : route_l, 'home': home_l, 'tot':qryset.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])}

        fac_m, route_m, home_m = fac.extra(select={'year': 'EXTRACT(year FROM date)','month': 'EXTRACT(month FROM date)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), route.extra(select={'year': 'EXTRACT(year FROM date)','month': 'EXTRACT(month FROM date)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), home.extra(select={'year': 'EXTRACT(year FROM date)','month': 'EXTRACT(month FROM date)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')

        ans_m = {'fac' : fac_m, 'route' : route_m, 'home': home_m, 'tot': qryset.extra(select={'year': 'EXTRACT(year FROM date)','month': 'EXTRACT(month FROM date)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')}

    resp['track'] = {'items_l':ans_l, 'items_m':ans_m, 'months' : months_between(start,end)}
    if req.REQUEST.has_key('csv') or req.REQUEST.has_key('excel'):  return reports_to_excel(qryset)  
    else:   return render_to_response('ubuzima/birth_report.html',
           resp, context_instance=RequestContext(req))
##END OF BIRTH TABLES, CHARTS, MAP

###START DEATH TABLES, CHARTS, MAP
@permission_required('ubuzima.can_view')
def death_report(req):

    resp = pull_req_with_filters(req)
    reports = matching_reports(req,resp['filters'])
    qryset = reports.filter(type__name = "Death")
    births = reports.filter(type__name='Birth', created__gte = resp['filters']['period']['start'], created__lte = resp['filters']['period']['end'])
    end = resp['filters']['period']['end']
    start = resp['filters']['period']['start']
    annot = resp['annot_l']
    locs = resp['locs']
    ans_l, ans_m = {},{}
    resp['reports'] = paginated(req, qryset)
    if qryset.exists():

        matde, chide, nebde = fetch_maternal_death(qryset),fetch_child_death(qryset),fetch_newborn_death(qryset)

        matde_l,chide_l,nebde_l = matde.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), chide.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), nebde.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])

        ans_l = {'matde' : matde_l, 'chide' : chide_l, 'nebde': nebde_l, 'tot': qryset.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]) }

        matde_m, chide_m, nebde_m = matde.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), chide.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), nebde.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')

        ans_m = {'matde' : matde_m, 'chide' : chide_m, 'nebde': nebde_m, 'tot': qryset.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')}

    resp['track'] = {'items_l':ans_l, 'items_m':ans_m, 'months' : months_between(start,end), 'bir_l': births.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), 'bir_m': births.extra(select={'year': 'EXTRACT(year FROM date)','month': 'EXTRACT(month FROM date)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')}

    if req.REQUEST.has_key('cat'):
        if req.GET['cat'] == 'cd':
            resp['title'] = 'Child Death'
            resp['reports'] = paginated(req, chide)
            return render_to_response('ubuzima/type.html', resp, context_instance=RequestContext(req))
        elif req.GET['cat'] == 'nd':
            resp['title'] = 'New Born Death'
            resp['reports'] = paginated(req, nebde)
            return render_to_response('ubuzima/type.html', resp, context_instance=RequestContext(req))
        elif req.GET['cat'] == 'md':
            resp['title'] = 'Maternal Death'
            resp['reports'] = paginated(req, matde)
            return render_to_response('ubuzima/type.html', resp, context_instance=RequestContext(req))
        

    if req.REQUEST.has_key('csv') or req.REQUEST.has_key('excel'):  return reports_to_excel(qryset)  
    else:   return render_to_response('ubuzima/death_report.html',
           resp, context_instance=RequestContext(req))

###END OF DEATH TABLES, CHARTS, MAP

###START RISK TABLES, CHARTS, MAP
@permission_required('ubuzima.can_view')
def risk_report(req):

    resp = pull_req_with_filters(req)
    reports = matching_reports(req,resp['filters'])
    resp['reports'] = reports
    qryset = reports.filter(type__name = "Risk")#(fields__in = Field.objects.filter(type__in = Field.get_risk_fieldtypes()))
    results = reports.filter(type__name = "Risk Result")
    allpatients = Patient.objects.filter( id__in = reports.values('patient'))
    end = resp['filters']['period']['end']
    start = resp['filters']['period']['start']
    annot = resp['annot_l']
    resp['reports'] = paginated(req, qryset)
    ans_l, ans_m = {},{}
    if qryset.exists():

        patients = allpatients.filter( id__in = qryset.values('patient'))
        patients_with_results = patients.filter( id__in = results.values('patient') )
        patients_with_pr = patients.filter(id__in = qryset.filter(fields__type__key__in = ['gs','mu','hd','rm']).values('patient'))
        patients_with_cr = patients.exclude(id__in = patients_with_pr.values_list('id'))
        
        #alerts = qryset.filter( id__in = TriggeredAlert.objects.filter( report__in = qryset).values('report'))
        #red_patients = patients.filter( id__in = alerts.values('patient'))
        #yes_alerts = qryset.filter( id__in = TriggeredAlert.objects.filter( report__in = qryset, trigger__destination = "AMB", response = 'YES').values('report'))
        #po_alerts = qryset.filter( id__in = TriggeredAlert.objects.filter( report__in = qryset, trigger__destination__in = ["SUP","DIS"], response = 'PO').values('report'))

        #patients_l, alerts_l, red_patients_l, yes_alerts_l, po_alerts_l = patients.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), alerts.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), red_patients.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), yes_alerts.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), po_alerts.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])

        patients_l, patients_with_results_l, patients_with_pr_l, patients_with_cr_l = patients.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), patients_with_results.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), patients_with_pr.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), patients_with_cr.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])

        
        #ans_l = {'pats' : patients_l, 'alts' : alerts_l, 'rpats': red_patients_l, 'yalts': yes_alerts_l, 'palts': po_alerts_l, 'tot': qryset.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]) }

        ans_l = {'pats' : patients_l, 'alts' : patients_with_results_l, 'rpats': patients_with_pr_l, 'yalts': patients_with_cr_l,'tot': qryset.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]) }

        #patients_m, alerts_m, red_patients_m, yes_alerts_m, po_alerts_m = qryset.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('patient',distinct = True)).order_by('year','month'), alerts.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), alerts.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('patient',distinct = True)).order_by('year','month'), yes_alerts.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), po_alerts.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')

        patients_m, patients_with_results_m, patients_with_pr_m, patients_with_cr_m = qryset.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('patient',distinct = True)).order_by('year','month'), results.filter(patient__in = patients_with_results).extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('patient',distinct = True)).order_by('year','month'), qryset.filter(patient__in = patients_with_pr).extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('patient',distinct = True)).order_by('year','month'), qryset.filter(patient__in = patients_with_cr).extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('patient',distinct = True)).order_by('year','month')

        #ans_m = {'pats' : patients_m, 'alts' : alerts_m, 'rpats': red_patients_m, 'yalts': yes_alerts_m, 'palts': po_alerts_m, 'tot': qryset.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')}

        ans_m = {'pats' : patients_m, 'alts' : patients_with_results_m, 'rpats': patients_with_pr_m, 'yalts': patients_with_cr_m, 'tot': qryset.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')}

    resp['track'] = {'items_l':ans_l, 'items_m':ans_m, 'months' : months_between(start,end), 'pats_l': allpatients.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), 'pats_m': reports.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('patient',distinct = True)).order_by('year','month')}
    
    if req.REQUEST.has_key('cat'):
        if req.GET['cat'] == 'pats':
            resp['title'] = 'Patients With Risk'
            resp['reports'] = paginated(req, patients)
            return render_to_response('ubuzima/patients.html', resp, context_instance=RequestContext(req))
        elif req.GET['cat'] == 'alts':
            resp['title'] = 'Patients With Result'
            resp['reports'] = paginated(req, patients_with_results)
            return render_to_response('ubuzima/patients.html', resp, context_instance=RequestContext(req))
        elif req.GET['cat'] == 'rpats':
            resp['title'] = 'Patients With Previous Risk'
            resp['reports'] = paginated(req, patients_with_pr)
            return render_to_response('ubuzima/patients.html', resp, context_instance=RequestContext(req))
        elif req.GET['cat'] == 'yalts':
            resp['title'] = 'Patients With Current Risk'
            resp['reports'] = paginated(req, patients_with_cr)
            return render_to_response('ubuzima/patients.html', resp, context_instance=RequestContext(req))
        

    if req.REQUEST.has_key('csv') or req.REQUEST.has_key('excel'):  return reports_to_excel(qryset)  
    else:   return render_to_response('ubuzima/risk_report.html',
           resp, context_instance=RequestContext(req))
###END OF RISK TABLES, CHARTS, MAP

###START RED ALERTS TABLES, CHARTS, MAP
@permission_required('ubuzima.can_view')
def red_alert_report(req):

    resp = pull_req_with_filters(req)
    reports = matching_reports(req,resp['filters'])
    resp['reports'] = reports
    qryset = reports.filter(type__name = "Red Alert")#(fields__in = Field.objects.filter(type__in = Field.get_risk_fieldtypes()))
    results = reports.filter(type__name = "Red Alert Result")
    patients, po_alerts = [], []
    allpatients = Patient.objects.filter( id__in = reports.values('patient'))
    end = resp['filters']['period']['end']
    start = resp['filters']['period']['start']
    annot = resp['annot_l']
    resp['reports'] = paginated(req, qryset)
    ans_l, ans_m = {},{}
    if qryset.exists():

        patients = allpatients.filter( id__in = qryset.values('patient'))
        red_patients = patients.filter( id__in = qryset.values('patient'))
        po_alerts = results.filter(id__in = Field.objects.filter(type__key__in  = ['mw','cw']).values('report'))

        patients_l, alerts_l, red_patients_l, yes_alerts_l, po_alerts_l = patients.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), qryset.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), red_patients.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), results.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), po_alerts.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])

        ans_l = {'pats' : patients_l, 'alts' : alerts_l, 'rpats': red_patients_l, 'yalts': yes_alerts_l, 'palts': po_alerts_l, 'tot': qryset.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]) }

        patients_m, alerts_m, red_patients_m, yes_alerts_m, po_alerts_m = qryset.filter(patient__in = patients).extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('patient',distinct = True)).order_by('year','month'), qryset.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), qryset.filter(patient__in = red_patients).extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('patient',distinct = True)).order_by('year','month'), results.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month'), po_alerts.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')

        ans_m = {'pats' : patients_m, 'alts' : alerts_m, 'rpats': red_patients_m, 'yalts': yes_alerts_m, 'palts': po_alerts_m, 'tot': qryset.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('id')).order_by('year','month')}

    resp['track'] = {'items_l':ans_l, 'items_m':ans_m, 'months' : months_between(start,end), 'pats_l': allpatients.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), 'pats_m': reports.extra(select={'year': 'EXTRACT(year FROM created)','month': 'EXTRACT(month FROM created)'}).values('year', 'month').annotate(number=Count('patient',distinct = True)).order_by('year','month')}

    if req.REQUEST.has_key('cat'):
        if req.GET['cat'] == 'rpats':
            resp['title'] = 'Patients With Red alert'
            resp['reports'] = paginated(req, patients)
            return render_to_response('ubuzima/patients.html', resp, context_instance=RequestContext(req))
        elif req.GET['cat'] == 'res':
            resp['title'] = 'Responded Alert'
            resp['reports'] = paginated(req, results)
            return render_to_response('ubuzima/type.html', resp, context_instance=RequestContext(req))
        elif req.GET['cat'] == 'palts':
            resp['title'] = 'Positive Outcomes'
            resp['reports'] = paginated(req, po_alerts)
            return render_to_response('ubuzima/type.html', resp, context_instance=RequestContext(req))
        
    if req.REQUEST.has_key('csv') or req.REQUEST.has_key('excel'):  return reports_to_excel(qryset)  
    else:   return render_to_response('ubuzima/red_alert_report.html',
           resp, context_instance=RequestContext(req))

###END OF RED ALERTS TABLES, CHARTS, MAP


##START OF CHILD TABLES, CHARTS, MAP
@permission_required('ubuzima.can_view')
def child_report(req):
    resp=pull_req_with_filters(req)
    resp['reports']=matching_reports(req,resp['filters'])
    end = resp['filters']['period']['end']
    start = resp['filters']['period']['start']
    qryset = resp['reports'].filter(type__name='Birth', date__gte = start, date__lte = end ).order_by('-date')
    annot=resp['annot_l']
    locs=resp['locs']
    resp['reports'] = paginated(req, qryset)
    return render_to_response('ubuzima/child_report.html',
           resp, context_instance=RequestContext(req))

@permission_required('ubuzima.can_view')
def view_chihe(req):
    resp=pull_req_with_filters(req)
    resp['reports']=matching_reports(req,resp['filters'])
    end = resp['filters']['period']['end']
    start = resp['filters']['period']['start']
    qryset = resp['reports'].filter(type__name='Child Health', created__gte = start, created__lte = end ).order_by('-date')
    annot=resp['annot_l']
    locs=resp['locs']
    resp['reports'] = paginated(req, qryset)

    chihe_reps = qryset.select_related('fields')
    vac_chihe_reps = fetch_vaccinated_stats(fetch_vaccinated_info(chihe_reps))
    
    ans=[]
    for v in FieldType.objects.filter(category=FieldCategory.objects.get(name='Vaccination Codes')).exclude(key__in = ['vc','vi','nv']):
        ans.append({'label':"Children vaccinated with %s"%v.description,'id':'%s'%v.key,'number':len(vac_chihe_reps[v.key])})
   
    ans.append({'label':"Children Vaccination Completed ",'id':'vc','number':len(vac_chihe_reps['vc'])})
    ans.append({'label':"Children Vaccination Not Completed",'id':'vi','number':len(vac_chihe_reps['vi'])})
    ans.append({'label':"Children Unimmunized",'id':'nv','number':len(vac_chihe_reps['nv'])})
    
    resp['track'] = ans
    return render_to_response('ubuzima/chihe.html', resp, context_instance = RequestContext(req))

@permission_required('ubuzima.can_view')
def chihe_stats(req, format, dat):
    resp=pull_req_with_filters(req)
    resp['reports']=matching_reports(req,resp['filters'])
    end = resp['filters']['period']['end']
    start = resp['filters']['period']['start']
    qryset = resp['reports'].filter(type__name='Child Health', created__gte = start, created__lte = end ).order_by('-date')
    annot=resp['annot_l']
    locs=resp['locs']
    
    resp['stattitle'] = {'%s'%dat:'%s' % FieldType.objects.get(key=dat).description}[dat]

    chihe_reps = qryset.select_related('fields')
    vac_chihe_reps = fetch_vaccinated_stats(fetch_vaccinated_info(chihe_reps))

    rez = []
    for v in vac_chihe_reps.keys():        
        if dat=='%s'%v:
            rez=vac_chihe_reps[v]
    if dat=='all':
        rez=fetch_vaccinated_info(chihe_reps)

    resp['reports'] = paginated(req, rez)
    
    if format == 'csv':
        return reports_to_excel(rez)
    else:
        return render_to_response('ubuzima/chihedetails.html', resp, context_instance = RequestContext(req))#return render_to_response(req, ('ubuzima/chihedetails.html'),
    #{'reports':paginated(req, rez, prefix = 'imp'),'start_date':date.strftime(flts['period']['start'], '%d.%m.%Y'),'usrloc':UserLocation.objects.get(user=req.user),
     #    'end_date':date.strftime(flts['period']['end'], '%d.%m.%Y'),
      #     'locationname':lxn,
   #'stattitle': {'%s'%dat:'Children Vaccinated with %s'%dat}[dat]})


##END OF CHILD TABLES, CHARTS, MAP
##START OF CHILD DETAILS TABLES, CHARTS, MAP
@permission_required('ubuzima.can_view')
def child_details_report(req, pk):
    resp=pull_req_with_filters(req)
    birth = Report.objects.get(pk = pk)
    child = birth.get_child()
    print child
    resp['reports'] = paginated(req, child['log'])
    resp['track'] = child
    return render_to_response('ubuzima/child_details.html',
           resp, context_instance=RequestContext(req))
##END OF CHILD DETAILS TABLES, CHARTS, MAP

##START OF ADMIN TABLES, CHARTS, MAP
@permission_required('ubuzima.can_view')
def admin_report(req):
    resp=pull_req_with_filters(req)
    annot = resp['annot_l']
    locs = resp['locs']
    ans_l, ans_m, rez = {}, {}, {}
    rez['%s__in'%annot.split(',')[1]] = [l.pk for l in locs]
    reporters = Reporter.objects.filter(** rez)
    active = reporters
    resp['reports'] = paginated(req, reporters)
    if reporters.exists() or active.exists():
        reporters_l, active_l = reporters.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0]), active.values(annot.split(',')[0],annot.split(',')[1]).annotate(number=Count('id')).order_by(annot.split(',')[0])

        ans_l = {'rep' : reporters_l, 'act' : active_l}

    resp['track'] = {'items_l':ans_l}
    return render_to_response('ubuzima/admin_report.html',
           resp, context_instance=RequestContext(req))
##END OF ADMIN TABLES, CHARTS, MAP

###START NUTRITION TABLES, CHARTS, MAP
@permission_required('ubuzima.can_view')
def my_report_loc(req,diced,alllocs=False):
    rez = {}
    pst = {}
    level = get_level(req)
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

    if level['level'] == 'Nation':  pst['nation__id'] = level['uloc'].nation.id
    elif level['level'] == 'Province':  pst['province__id'] = level['uloc'].province.id
    elif level['level'] == 'District':  pst['district__id'] = level['uloc'].district.id
    elif level['level'] == 'HealthCentre':  pst['location__id'] = level['uloc'].health_centre.id

    return [rez,pst]

@permission_required('ubuzima.can_view')
def my_field_loc(req,diced,alllocs=False):
    rez = {}
    pst = {}
    level = get_level(req)
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

    if level['level'] == 'Nation':  pst['nation__id'] = level['uloc'].nation.id
    elif level['level'] == 'Province':  pst['province__id'] = level['uloc'].province.id
    elif level['level'] == 'District':  pst['district__id'] = level['uloc'].district.id
    elif level['level'] == 'HealthCentre':  pst['location__id'] = level['uloc'].health_centre.id

    return [rez,pst]

@permission_required('ubuzima.can_view')
def my_report_loc(req,diced,alllocs=False):
    rez = {}
    pst = {}
    level = get_level(req)
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

    if level['level'] == 'Nation':  pst['nation__id'] = level['uloc'].nation.id
    elif level['level'] == 'Province':  pst['province__id'] = level['uloc'].province.id
    elif level['level'] == 'District':  pst['district__id'] = level['uloc'].district.id
    elif level['level'] == 'HealthCentre':  pst['location__id'] = level['uloc'].health_centre.id

    return [rez,pst]

@permission_required('ubuzima.can_view')
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
    cg = Calculator(adjust_height_data=False, adjust_weight_scores=False)
    wfa = lhfa = wfl = None
    if not child or type(child) != dict: return {'wfa': wfa, 'lhfa': lhfa, 'wfl': wfl}
    if child['weight'] and child['valid_age'] and child['valid_gender']: wfa = cg.zscore_for_measurement('wfa', child['weight'], child['valid_age'], child['valid_gender'])
    if child['height'] and child['valid_age'] and child['valid_gender']: lhfa = cg.zscore_for_measurement('lhfa', child['height'], child['valid_age'], child['valid_gender'])
    if child['weight'] and child['valid_age'] and child['valid_gender'] and child['height']: wfl = cg.zscore_for_measurement('lhfa', child['weight'], child['valid_age'], child['valid_gender'], child['height'])

    return {'wfa': wfa, 'lhfa': lhfa, 'wfl': wfl}


@permission_required('ubuzima.can_view')
def view_nutrition_charts(req):
    return HttpResponse(json.dumps(growth_chart_data(req)), content_type='application/json')

@permission_required('ubuzima.can_view')
def growth_chart_data(req):
    resp=pull_req_with_filters(req)
    flts = resp['filters']
    pst = my_report_filters(req, flts)
    locz = my_report_loc(req,flts)
    reps = Report.objects.filter(type__pk=3, **pst).filter(**locz[0]).filter(**locz[1])
    #print pst, locz[0], locz[1], reps.count()
    boys = []
    girls = []
    unknown = []
    for rep in reps:
        child = rep.get_child()
        child_data = {}
        chart_data = {}
        for f in rep.fields.all():
            if f.type.key == u'child_number':
                child_data.update({f.type.key: int(f.value)})
            if f.type.key == u'child_weight':
                chart_data.update({"weight": int(f.value)})
            if f.type.key in [u'child_weight', u'child_height', u'muac']:
                child_data.update({f.type.key: f.value.to_eng_string()})
        if len(child_data) > 0:
            if child['birth']['date'] is not None:
                child_data.update({'birth_date': child['birth']['date'].isoformat()})
            # FIXME child['birth']['weight'] is not the weight at birth!
            #if child['birth']['weight'] is not None:
            #    child_data.update({'birth_weight': child['birth']['weight'].value.to_eng_string()})
            child_data.update({'national_id': rep.patient.national_id})
            chart_data.update({'id': int(rep.patient.national_id)})
            child_data.update({'district_id': int(rep.patient.district_id)})
            child_data.update({'report_type': rep.type.name})
            if rep.date is not None:
                child_data.update({'report_date': rep.created.date().isoformat()})
            if rep.get_sex() is not None:
                child_data.update({'sex': rep.get_sex()})
            if ('report_date' in child_data) and ('birth_date' in child_data):
                age_in_months = (rep.created.date() - child['birth']['date']).days / 30.4374
                child_data.update({'age_in_months': age_in_months})
                chart_data.update({'age': age_in_months})
            if 'sex' in child_data:
                # TODO not sure if these are correct bc none of the cbn
                # patients have a sex
                chart_data.update({'sex': child_data['sex']})
                if child_data['sex'].lower() in ['male', 'bo', 'boy']:
                    boys.append(chart_data)
                else:
                    girls.append(chart_data)
            else:
                if child['id']['chino'] is not None:
                    """
                    # TODO this is super slow and doesnt find any sex for any
                    # of the cbn cases, so skip for now...
                    # see if child's sex is noted in another report
                    sexes = []
                    for rep in Report.objects.filter(patient__national_id=rep.patient.national_id):
                        if rep.get_child_id() is not None and rep.get_child_id().get('chino') == child['id']['chino']:
                            if rep.get_child() is not None and rep.get_child().get('birth') is not None:
                                sexes.append(rep.get_child().get('birth').get('sex'))
                    sexes = list(set(sexes))
                    if len(sexes) == 1 and sexes[0] is not None:
                        child_data.update({'sex': sexes[0]})
                        chart_data.update({'sex': sexes[0]})
                        # TODO not sure if these are correct bc none of the cbn
                        # patients have a sex
                        if sexes[0].lower() in ['male', 'bo', 'boy']:
                            boys.append(chart_data)
                        else:
                            girls.append(chart_data)
                    """
                    unknown.append(chart_data)
    return {'boys': boys, 'girls': girls, 'unknown': unknown}


@permission_required('ubuzima.can_view')
def view_nutrition(req, indic, format = 'html'):
    resp=pull_req_with_filters(req)
    filters = resp['filters']
    rez = my_filters(req, filters)
    #indicator = FieldType.objects.get(id = indic)
    #pts = Field.objects.filter( type = indicator, **rez)
    hindics = nutrition_indicators(req,resp['filters'])
    pts = hindics['desc'][indic]
    resp['hindics'] = paginated(req, hindics['desc'][indic])
    heads   = ['Reporter', 'Location', 'Patient', 'Type', 'Date']
    resp['headers'] = heads
    resp['reports'] = paginated(req, pts)
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
    return render_to_response('ubuzima/nutrition.html', resp, context_instance=RequestContext(req))

@permission_required('ubuzima.can_view')
def nutrition(req):
    resp=pull_req_with_filters(req)
    resp['chart_data'] = growth_chart_data(req)
    return render_to_response("ubuzima/nutrition_dash.html", resp, context_instance=RequestContext(req))

@permission_required('ubuzima.can_view')
def nutrition_data(req):
    resp=pull_req_with_filters(req)
    hindics = nutrition_indicators(req,resp['filters'])
    resp['hindics'] = paginated(req, hindics['home'])
    return render_to_response("ubuzima/nutrition_data.html", resp, context_instance=RequestContext(req))
###END OF NUTRITION TABLES, CHARTS, MAP


###VIEW UBUZIMA EMERGENCY ROOM####
@permission_required('ubuzima.can_view')
def emergency_room(req):
    resp=pull_req_with_filters(req)
    resp['filters']['period']['end'] = datetime.date.today()
    resp['filters']['period']['start'] = datetime.date.today() - timedelta(days = 1)
    pst = my_report_filters(req, resp['filters'])

    red = Report.objects.filter(type__name = 'Red Alert', **pst).order_by('-id')
    red_res = Report.objects.filter(type__name = 'Red Alert Result', patient__in = red.values('patient'), **pst)
    red_res_po = red_res.exclude( fields__type__key__in = ['ms','cs'])
    red_res_ne = red_res.exclude(  fields__type__key__in = ['mw','cw'])
    red_unres = red.exclude( patient__in = red_res.values('patient'))

    
    resp['data'] = red.values('location__name','location__pk').annotate(total = Count('id')).order_by('location__name')
        
    resp['unres'] = red_unres
    if red_unres.exists():  resp['last'] = red_unres[0]
    for d in resp['data']:
        d['red_res_po'] = red_res_po.filter(location__pk = d['location__pk']).count()
        d['red_res_ne'] = red_res_ne.filter(location__pk = d['location__pk']).count()
        d['red_unres'] = red_unres.filter(location__pk = d['location__pk']).count()
        d['red_unres_r'] = red_unres.filter(location__pk = d['location__pk'])
    return render_to_response("ubuzima/emergency_room.html", resp, context_instance=RequestContext(req))


### END OF EMERGENCY ROOM #######

#### END OF IBIBARI DASHBOARD



###PREGNANCY CALENDAR ####

def json_response(func):
    """
    A decorator thats takes a view response and turns it
    into json. If a callback is added through GET or POST
    the response is JSONP.
    """
    
    def decorator(request, *args, **kwargs):        
        objects = func(request, *args, **kwargs)
        
        if isinstance(objects, HttpResponse):
            
            return objects
        try:
            if isinstance(objects, QuerySet):
                data = serializers.serialize("json", objects)
            else:
                data = simplejson.dumps(objects, cls=DjangoJSONEncoder)
            if 'callback' in request.REQUEST:
                # a jsonp response!
                data = '%s(%s);' % (request.REQUEST['callback'], data)
                return HttpResponse(data, "text/javascript")
        except:
            data = simplejson.dumps(str(objects), cls=DjangoJSONEncoder)
        return HttpResponse(data, "application/json")
    try:    
        return decorator
    except Exception, e:    print e

@permission_required('ubuzima.can_view')
def pregnancy_calendar_data(request):
    
    showdate_str = request.POST['showdate']###in the form mm/dd/year
    showdate_array = showdate_str.split("/")
    yyyy, mm, dd = showdate_array[2], showdate_array[0], showdate_array[1]
    showdate = datetime.date(int(yyyy), int(mm), int(dd))

    viewtype = request.POST['viewtype']

    st, et = None, None
    if viewtype == 'month':
        st = datetime.datetime(showdate.year, showdate.month, 1,0,0)
        et = datetime.datetime(showdate.year, showdate.month + 1, 1,23,59) - timedelta(days = 1)

    elif viewtype == 'week':
        start_week = showdate - datetime.timedelta(showdate.weekday())
        end_week = start_week + datetime.timedelta(7)
        st = datetime.datetime(start_week.year, start_week.month, start_week.day,0,0)
        et = datetime.datetime(end_week.year, end_week.month, end_week.day,23,59)

    elif viewtype == 'day':
        st = datetime.datetime(showdate.year, showdate.month, showdate.day,0,0)
        et = datetime.datetime(showdate.year, showdate.month, showdate.day + 1,23,59)   

    events = []
    edd = Report.objects.filter(type__name = 'Pregnancy', edd_date__gte = st , edd_date__lte = et).order_by('edd_date').values('edd_date').annotate(total = Count('id'))
    i = 1
    for ed in edd:
        try:
            events.append(["%d" % i, "Expected Deliveries: %d" % ed['total'], ed['edd_date'].strftime('%m/%d/%Y %H:%M'), ed['edd_date'].strftime('%m/%d/%Y %H:%M'), "1", 0, 0, "9", 1, "Rwanda", "" ])
            i = i + 1
        except Exception, e:    print e#continue 
    
    pdata = { 'events' : events, 'issort' : True, 'start' : st.strftime('%m/%d/%Y %H:%M'), 'end' : et.strftime('%m/%d/%Y %H:%M'), 'error' : None}    

    #data = {"events":[["1","Pregnancy","04/19/2013 00:00","04/30/2013 00:00","1",0,0,"Green",1,"Musanze",""],["2","Pregnancy","04/18/2013 00:00","04/18/2013 00:00","1",0,0,"Red",1,"Musanze",""],["3","Pregnancy","04/19/2013 00:00","04/19/2013 00:00","1",0,0,"Green",1,"Musanze",""],["4","Pregnancy","04/30/2013 00:00","04/30/2013 00:00","1",0,0,"Red",1,"Musanze",""],["5","Pregnancy","04/23/2013 00:00","04/23/2013 00:00","1",0,0,"Green",1,"Musanze",""],["6","Pregnancy","04/16/2013 00:00","04/16/2013 00:00","1",0,0,"13",1,"Musanze",""],["7","Birth","04/16/2013 00:00","04/16/2013 00:00","1",0,0,"9",1,"Kacyiru",""]],"issort":True,"start":"04/01/2013 00:00","end":"04/30/2013 23:59","error":None} 
    
    #print pdata, "\n\n", data, st, et
    return HttpResponse(json.dumps(pdata), "application/json")

@permission_required('ubuzima.can_view')
def pregnancy_calendar(req):
    resp=pull_req_with_filters(req)
    
    if req.REQUEST.has_key('method'):
        return pregnancy_calendar_data(req)
    return render_to_response("ubuzima/pregnancy_calendar.html", resp,context_instance=RequestContext(req))
    

###END OF PREGNANCY CALENDAR ####
