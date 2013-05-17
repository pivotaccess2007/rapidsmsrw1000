#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import unicodecsv as csv
import xlwt

from datetime import date, timedelta

from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from rapidsmsrw1000.apps.chws.models import *
from rapidsmsrw1000.apps.ubuzima.models import *

#wbk = xlwt.Workbook()
#sheet.write(0,0,"ReportID")
#sheet.write(0,1,"Date")
#sheet.write(0,2,"Location")
#sheet.write(0,3,"District")
#sheet.write(0,4,"Type")
#sheet.write(0,5,"Reporter")
#sheet.write(0,6,"Patient")
#sheet.write(0,7,"Message")


#row = 1
#for r in reports:
#  sheet.write(row,0,r.pk)
#  sheet.write(row,1,"%d.%d.%d" % (r.created.day,r.created.month,r.created.year))
#  sheet.write(row,2,r.location.name)
#  sheet.write(row,3,r.location.parent.parent.name)
#  sheet.write(row,4,r.type.name)
#  sheet.write(row,5,r.reporter.alias)
#  sheet.write(row,6,r.patient.national_id)
#  sheet.write(row,7,r.summary())
#  row = row+1

#wbk.save('xlwt.xls')####This allows the workbook to be saved on the disk

def create_workbook():

    return xlwt.Workbook()

def create_worksheet( workbook, name = "Export"):

    return workbook.add_sheet(name)

def create_heads(sheet, heads):
    """sheet = xlwt sheet object ... eg sheet = xlwt.Workbook().add_sheet("Reports"),
           heads =  a list of headers ... eg : heads = ['ReportID','Date','Location','District','Type','Reporter','Patient','Message'] """

    hl = len(heads)
    row, col = 0, 0
    for h in heads:
        if col == hl:
            break
        else:
            sheet.write(row, col, heads[col])
            col = col + 1

    return sheet



def create_content(sheet, row, content_list):
    """sheet = xlwt sheet object ... eg sheet = xlwt.Workbook().add_sheet("Reports"),
           heads =  a list of headers ... eg : content_list = [r.id, "%d.%d.%d" % (r.created.day,r.created.month,r.created.year),r.location.name,r.location.parent.parent.name,r.type.name,r.reporter.alias,r.patient.national_id, r.summary()] """


    cl = len(content_list)
    col = 0
    for item in content_list:
        if col == cl:
            break
        else:
            sheet.write(row, col, content_list[col])
            col = col + 1


    return sheet

def heading_report(report):
    heads = ['ReportID','Date','Facility', 'District', 'Province','Type','Reporter','Patient', 'LMP', 'DOB', 'VisitDate',' ANCVisit','NBCVisit','PNCVisit','MotherWeight','MotherHeight','ChildWeight','ChildHeight','MUAC', 'ChilNumber','Gender', 'Gravidity','Parity', 'VaccinationReceived' , 'VaccinationCompletion','Breastfeeding', 'Intevention', 'Status','Toilet','Handwash' , 'Located','Symptoms']

    dob = lmp = visit = anc = nbc = pnc = mother_w = child_w = mother_h = child_h = muac = chino = gender = gr = pr = vr = vc = bf = interv = st = toi = hw = loc = sym = ""

    try:
        mother_wf = report.fields.filter(type__key = 'mother_weight')
        for s in mother_wf:
            mother_w = mother_w.join("%d" % s.value)
    except: pass
    try:
        mother_hf = report.fields.filter(type__key = 'mother_height')
        for s in mother_hf:
            mother_h = mother_h.join("%d" % s.value)
    except: pass
    try:
        child_wf = report.fields.filter(type__key = 'child_weight')
        for s in child_wf:
            child_w = child_w.join("%d" % s.value)
    except: pass
    try:
        child_hf = report.fields.filter(type__key = 'child_height')
        for s in child_hf:
            child_h = child_h.join("%d" % s.value)
    except: pass
    try:
        ancf = report.fields.filter(type__key__in = ['anc2','anc3','anc4'])
        for s in ancf:
            anc = anc.join("%s" % s.type.description)
    except: pass
    try:
        pncf = report.fields.filter(type__key__in = ['pnc1','pnc2','pnc3'])
        for s in pncf:
            pnc = pnc.join("%s" % s.type.description)
    except: pass
    try:
        nbcf = report.fields.filter(type__key__in = ['nbc1','nbc2','nbc3','nbc4','nbc5'])
        for s in nbcf:
            nbc = nbc.join("%s" % s.type.description)
    except: pass
    try:
        muacf = report.fields.filter(type__key = 'muac')
        for s in muacf:
            muac = muac.join("%d" % s.value)
    except: pass
    try:
        chinof = report.fields.filter(type__key = 'child_number')
        for s in chinof:
            chino = chino.join("%d" % s.value)
    except: pass
    try:
        genderf = report.fields.filter(type__key__in = ['gi','bo'])
        for s in genderf:
            gender = gender.join("%s" % s.type.description)
    except: pass
    try:
        grf = report.fields.filter(type__key = 'gravity')
        for s in grf:
            gr = gr.join("%d" % s.value)
    except: pass

    try:
        prf = report.fields.filter(type__key = 'parity')
        for s in prf:
            pr = pr.join("%d" % s.value)
    except: pass
    try:
        vrf = report.fields.filter(type__key__in = ['v1','v2','v3','v4','v5','v6'])
        for s in vrf:
            vr = vr.join("%s" % s.type.description)
    except: pass
    try:
        vcf = report.fields.filter(type__key__in = ['vc', 'vi', 'nv'])
        for s in vcf:
            vc = vc.join("%s" % s.type.description)
    except: pass
    try:
        bff = report.fields.filter(type__key__in = ['ebf','cbf','nb'])
        for s in bff:
            bf = bf.join("%s" % s.type.description)
    except: pass
    try:

        intervf = report.fields.filter(type__category__name = 'Intervention Codes')
        for s in intervf:
            interv = interv.join("%s" % s.type.description)
    except: pass
    try:
        locf = report.fields.filter(type__category__name = 'Location Codes')
        for s in locf:
            loc = loc.join("%s" % s.type.description)
    except: pass
    try:
        stf = report.fields.filter(type__category__name = 'Results Codes')
        for s in stf:
            st = st+s.type.description+", "
    except: pass
    try:
        hwf = report.fields.filter(type__key__in = ['hw','nh'])
        for s in hwf:
            hw = hw.join("%s" % s.type.description)
    except: pass
    try:
        toif = report.fields.filter(type__key__in = ['to', 'nt'])
        for s in toif:
            toi = toi.join("%s" % s.type.description)
    except: pass

    try:
        symf = report.fields.filter(type__category__name__in = ['Risk Codes' , 'Red Alert Codes'])
        for s in symf:
            sym = sym+s.type.description+", "
    except: pass
    print 'id:%s'%report.id, 'date:%s'%read_date(report.created), 'fac:%s'%report.location.name, 'dist:%s'%report.district.name, 'prv:%s'%report.province.name, 'rty:%s'%report.type.name , 'rnid:%s'%report.reporter.telephone_moh, 'pnid:%s'%report.patient.national_id , 'lmp:%s'%lmp, 'dob:%s'%dob, 'visit:%s'%visit, 'anc:%s'%anc, 'nbc:%s'%nbc, 'pnc:%s'%pnc, 'm_w:%s'%mother_w, 'm_h:%s'%mother_h, 'c_w:%s'%child_w, 'c_w:%s'%child_h, 'muac:%s'%muac, 'chino:%s'%chino, 'gender:%s'%gender, 'gr:%s'%gr, 'pr:%s'%pr, 'vr:%s'%vr, 'vc:%s'%vc, 'bf:%s'%bf, 'interv:%s'%interv, 'st:%s'%st, 'toi:%s'%toi, 'hw:%s'%hw, 'loc:%s'%loc, 'sym:%s'%sym


    if report.type.name == 'Birth': dob = read_date(report.date)
    elif report.type.name == 'Pregnancy': lmp = read_date(report.date)
    elif report.type.name == 'ANC': visit = read_date(report.date)
    else:   dob = read_date(report.date)

    content = [report.id, read_date(report.created), report.location.name, report.district.name, report.province.name, report.type.name , report.reporter.national_id, report.patient.national_id , lmp, dob, visit, anc,nbc, pnc, mother_w, mother_h, child_w, child_h, muac, chino, gender, gr, pr, vr, vc, bf, interv, st, toi, hw, loc, sym ]

    return {'heads' : heads, 'content' : content}

def reports_to_excel(reports):
    maquis = heading_report(reports[1])
    workbook = create_workbook()
    sheet = create_worksheet(workbook, "reports")
    sheet = create_heads(sheet, maquis['heads'])
    row   = 1
    for report in reports:
        sheet  = create_content(sheet, row, heading_report(report)['content'])

        row = row + 1

    response = HttpResponse(mimetype = "application/ms-excel")
    response['Content-Disposition'] = 'attachment; filename = reports.xls'
    workbook.save(response)
    return response

def read_date(date):
    try: return "%d/%d/%d" %  (date.day, date.month, date.year)
    except: return ""


def matching_reports(req, diced, alllocs = False):
    rez = {}
    pst = {}
    level = get_level(req)
    try:
        rez['created__gte'] = diced['period']['start']
        rez['created__lte'] = diced['period']['end']+timedelta(1)
    except KeyError:
        pass



    try:
        loc = int(req.REQUEST['location'])
        rez['location__id'] = loc

    except KeyError:
        try:
            dst=int(req.REQUEST['district'])
            rez['district__id'] = dst
        except KeyError:
            try:
                dst=int(req.REQUEST['province'])
                rez['province__id'] = dst
            except KeyError:    pass

    if level['level'] == 'Nation':  pst['nation__id'] = level['uloc'].nation.id
    elif level['level'] == 'Province':  pst['province__id'] = level['uloc'].province.id
    elif level['level'] == 'District':  pst['district__id'] = level['uloc'].district.id
    elif level['level'] == 'HealthCentre':  pst['location__id'] = level['uloc'].health_centre.id

    if rez:
        ans = Report.objects.filter(**rez).order_by("-created")
    else:
       ans = Report.objects.all().order_by("-created")

    if pst:
        ans = ans.filter(**pst).order_by("-created")
    return ans

def location_name(req):
    ans = []
    try:
        uloc = get_user_location(req)
        if uloc.health_centre:
            prv = uloc.health_centre.province
            ans.append(prv.name + ' Province')
            dst = uloc.health_centre.district
            ans.append(dst.name + ' District')
            loc = uloc.health_centre
            ans.append(loc.name)
        elif uloc.district:
            prv = uloc.district.province
            ans.append(prv.name + ' Province')
            dst = uloc.district
            ans.append(dst.name + ' District')
            loc = HealthCentre.objects.get(id = int(req.REQUEST['loc']))
            ans.append(loc.name)
        elif uloc.province:
            prv = uloc.province
            ans.append(prv.name + ' Province')
            dst = District.objects.get(id = int(req.REQUEST['district']))
            ans.append(dst.name + ' District')
            loc = HealthCentre.objects.get(id = int(req.REQUEST['loc']))
            ans.append(loc.name)
        else:

            prv = Province.objects.get(id = int(req.REQUEST['province']))
            ans.append(prv.name + ' Province')
            dst = District.objects.get(id = int(req.REQUEST['district']))
            ans.append(dst.name + ' District')
            loc = HealthCentre.objects.get(id = int(req.REQUEST['loc']))
            ans.append(loc.name)
    except KeyError, DoesNotExist:
        pass
    ans.reverse()

    return ', '.join(ans)

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


def get_level(req):
    try:
        uloc = req.user.hcuser.all()[0]
        level = ""
        if uloc.nation:
            level = "Nation"
        elif uloc.province:
            level = "Province"
        elif uloc.district:
            level = "District"
        elif uloc.health_centre:
            level = "HealthCentre"
        return {'level': level, 'uloc': uloc}
    except:
        return None


def reporter_fresher(req):
    pst = {}
    try:
        level = get_level(req)
        if level['level'] == 'Nation':
            pst['nation__id'] = level['uloc'].nation.id
        elif level['level'] == 'Province':
            pst['province__id'] = level['uloc'].province.id
        elif level['level'] == 'District':
            pst['district__id'] = level['uloc'].district.id
        elif level['level'] == 'HealthCentre':
            pst['health_centre__id'] = level['uloc'].health_centre.id
    except:
        pass
    return pst


def default_location(req):
    try:
        uloc = get_user_location(req)
        hcs = None

        if uloc.nation:
            sel = int(req.REQUEST['location']) if req.REQUEST.has_key('location') else 1
            hcs = HealthCentre.objects.filter(nation = uloc.nation).extra(select = {'selected':'id = %d' % (sel,)}).order_by('name')
        elif uloc.province:
            sel = int(req.REQUEST['location']) if req.REQUEST.has_key('location') else 1
            hcs = HealthCentre.objects.filter(province = uloc.province).extra(select = {'selected':'id = %d' % (sel,)}).order_by('name')
        elif uloc.district:
            sel = int(req.REQUEST['location']) if req.REQUEST.has_key('location') else 1
            hcs = HealthCentre.objects.filter(district = uloc.district).extra(select = {'selected':'id = %d' % (sel,)}).order_by('name')
        elif uloc.health_centre:
            sel = int(req.REQUEST['location']) if req.REQUEST.has_key('location') else uloc.health_centre.id
            hcs = HealthCentre.objects.filter(pk = uloc.health_centre.id).extra(select = {'selected':'id = %d' % (sel,)}).order_by('name')

        if req.REQUEST.has_key('province'): hcs = hcs.filter(province__id = int(req.REQUEST['province']))
        if req.REQUEST.has_key('district'): hcs = hcs.filter(district__id = int(req.REQUEST['district']))
        if req.REQUEST.has_key('location'): hcs = hcs.filter(id = int(req.REQUEST['location']))

        return hcs
    except UserLocation.DoesNotExist, e:
        return []

def default_province(req):
    uloc = get_user_location(req)
    prvs = None
    try:

        if uloc:
            if uloc.nation:
                sel = int(req.REQUEST['province']) if req.REQUEST.has_key('province') else 0
                prvs = Province.objects.all().extra(select = {'selected':'id = %d' % (sel,)}).order_by('name')

            elif uloc.province:
                sel = int(req.REQUEST['province']) if req.REQUEST.has_key('province') else uloc.province.id
                prvs = Province.objects.filter( pk = uloc.province.id ).extra(select = {'selected':'id = %d' % (sel,)}).order_by('name')

            elif uloc.district:
                sel = int(req.REQUEST['province']) if req.REQUEST.has_key('province') else uloc.district.province.id
                prvs = Province.objects.filter( pk = uloc.district.province.id ).extra(select = {'selected':'id = %d' % (sel,)}).order_by('name')

            elif uloc.heath_centre:
                sel = int(req.REQUEST['province']) if req.REQUEST.has_key('province') else uloc.health_centre.id
                prvs = Province.objects.filter( pk = uloc.health_centre.province.id ).extra(select = {'selected':'id = %d' % (sel,)}).order_by('name')

            if req.REQUEST.has_key('province'): prvs = prvs.filter(id = int(req.REQUEST['province']))
            return prvs.exclude(name = 'TEST')
        else:
            return []

    except Exception, e:
        return []

def default_district(req):
    uloc = get_user_location(req)
    dsts = None
    try:

        if uloc:
            if uloc.nation:
                sel = int(req.REQUEST['district']) if req.REQUEST.has_key('district') else 1
                dsts = District.objects.all().extra(select = {'selected':'id = %d' % (sel,)}).order_by('name')

            elif uloc.province:
                sel = int(req.REQUEST['district']) if req.REQUEST.has_key('district') else 1
                dsts = District.objects.filter( province = uloc.province ).extra(select = {'selected':'id = %d' % (sel,)}).order_by('name')

            elif uloc.district:
                sel = int(req.REQUEST['district']) if req.REQUEST.has_key('district') else uloc.district.id
                dsts = District.objects.filter( pk = uloc.district.id ).extra(select = {'selected':'id = %d' % (sel,)}).order_by('name')

            elif uloc.heath_centre:
                sel = int(req.REQUEST['district']) if req.REQUEST.has_key('district') else uloc.health_centre.district.id
                dsts = District.objects.filter( pk = uloc.health_centre.district.id ).extra(select = {'selected':'id = %d' % (sel,)}).order_by('name')

            if req.REQUEST.has_key('province'): dsts = dsts.filter(province__id = int(req.REQUEST['province']))
            #if req.REQUEST.has_key('district'): dsts = dsts.filter(id = int(req.REQUEST['district']))
            return dsts
        else:
            return []

    except Exception, e:
        return []


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
    uloc = get_object_or_404(UserLocation, user=req.user)
    return uloc


def csv_chws(chws,group):
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s-export-%s.csv' % (group.name,datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S'))
    writer = csv.writer(response)
    writer.writerow(['IZINA RY\'UMURYANGO','ANDI MAZINA','ICYO AKORA(Binome, ASM)','IGITSINA(F:Gore,M:Gabo)',\
                                    'AMASHULI YIZE(P:Primaire, S:Secondaire, U:University, N:Ntabwo yize)','ITARIKI Y\'AMAVUKO(DD/MM/AAAA)',\
                                'ITARIKI Y\'UBUJYANAMA(AAAA:Umwaka)','NUMERO Y\'INDANGAMUNTU', 'NUMERO YA TELEPHONE YAHAWE NA MNISANTE', 'UMUDUGUDU',\
                                 'AKAGARI', 'SECTEUR', 'CENTRE DE SANTE(Ivuriro)', 'HOPITAL(Ibitaro)', 'DISTRICT(Akarere)'])

    for r in chws:

        surname = given_name = role = sex = education_level = date_of_birth = join_date = national_id = telephone_moh = \
                 village = cell = sector = district = health_centre = referral_hospital = ""

        try:    surname = r.surname
        except: pass
        try:    given_name = r.given_name
        except: pass
        try:    role = r.role.name
        except: pass
        try:    sex = r.sex
        except: pass
        try:    education_level = r.education_level
        except: pass
        try:    date_of_birth = "%d/%d/%d" % (r.date_of_birth.day, r.date_of_birth.month, r.date_of_birth.year )
        except: pass
        try:    join_date = "%d/%d/%d" % (r.join_date.day, r.join_date.month, r.join_date.year)
        except: pass
        try:    national_id = r.national_id
        except: pass
        try:    telephone_moh = r.telephone_moh
        except: pass
        try:    village = r.village.name
        except: pass
        try:    cell = r.cell.name
        except: pass
        try:    sector = r.sector.name
        except: pass
        try:    district = r.district.name
        except: pass
        try:    health_centre = r.health_centre.name
        except: pass
        try:    referral_hospital = r.referral_hospital.name
        except: pass

        writer.writerow([surname, given_name, role, sex, \
                                                education_level, date_of_birth , join_date, national_id,\
                                                 telephone_moh, village, cell, sector,\
                                                 health_centre, referral_hospital, district])


    return response
def excel_chws(chws):
    workbook = create_workbook()
    sheet = create_worksheet(workbook, "reporters")

    sheet = create_heads(sheet, ['IZINA RY\'UMURYANGO','ANDI MAZINA','ICYO AKORA(Binome, ASM)','IGITSINA(F:Gore,M:Gabo)',\
                                    'AMASHULI YIZE(P:Primaire, S:Secondaire, U:University, N:Ntabwo yize)','ITARIKI Y\'AMAVUKO(DD/MM/AAAA)',\
                                'ITARIKI Y\'UBUJYANAMA(AAAA:Umwaka)','NUMERO Y\'INDANGAMUNTU', 'NUMERO YA TELEPHONE YAHAWE NA MNISANTE', 'UMUDUGUDU',\
                                 'AKAGARI', 'SECTEUR', 'CENTRE DE SANTE(Ivuriro)', 'HOPITAL(Ibitaro)', 'DISTRICT(Akarere)'])
    row   = 1

    for r in chws:

        surname = given_name = role = sex = education_level = date_of_birth = join_date = national_id = telephone_moh = \
                 village = cell = sector = district = health_centre = referral_hospital = ""

        try:    surname = r.surname
        except: pass
        try:    given_name = r.given_name
        except: pass
        try:    role = r.role.name
        except: pass
        try:    sex = r.sex
        except: pass
        try:    education_level = r.education_level
        except: pass
        try:    date_of_birth = "%d/%d/%d" % (r.date_of_birth.day, r.date_of_birth.month, r.date_of_birth.year )
        except: pass
        try:    join_date = "%d/%d/%d" % (r.join_date.day, r.join_date.month, r.join_date.year)
        except: pass
        try:    national_id = r.national_id
        except: pass
        try:    telephone_moh = r.telephone_moh
        except: pass
        try:    village = r.village.name
        except: pass
        try:    cell = r.cell.name
        except: pass
        try:    sector = r.sector.name
        except: pass
        try:    district = r.district.name
        except: pass
        try:    health_centre = r.health_centre.name
        except: pass
        try:    referral_hospital = r.referral_hospital.name
        except: pass

        sheet  = create_content(sheet, row, [surname, given_name, role, sex, \
                                                education_level, date_of_birth , join_date, national_id,\
                                                 telephone_moh, village, cell, sector,\
                                                 health_centre, referral_hospital, district])

        row = row + 1

    response = HttpResponse(mimetype = "application/ms-excel")
    response['Content-Disposition'] = 'attachment; filename = reporters.xls'
    workbook.save(response)
    return response

def excel_regs_confirms(regs):
    workbook = create_workbook()
    sheet = create_worksheet(workbook, "reporters")

    sheet = create_heads(sheet, ['IZINA RY\'UMURYANGO','ANDI MAZINA','ICYO AKORA(Binome, ASM)','IGITSINA(F:Gore,M:Gabo)',\
                                    'AMASHULI YIZE(P:Primaire, S:Secondaire, U:University, N:Ntabwo yize)','ITARIKI Y\'AMAVUKO(DD/MM/AAAA)',\
                                'ITARIKI Y\'UBUJYANAMA(AAAA:Umwaka)','NUMERO Y\'INDANGAMUNTU', 'NUMERO YA TELEPHONE YAHAWE NA MNISANTE', 'UMUDUGUDU',\
                                 'AKAGARI', 'SECTEUR', 'CENTRE DE SANTE(Ivuriro)', 'HOPITAL(Ibitaro)', 'DISTRICT(Akarere)'])
    row   = 1

    for r in regs:

        surname = given_name = role = sex = education_level = date_of_birth = join_date = national_id = telephone_moh = \
                 village = cell = sector = district = health_centre = referral_hospital = ""

        try:    surname = r.reporter.surname
        except: pass
        try:    given_name = r.reporter.given_name
        except: pass
        try:    role = r.reporter.role.name
        except: pass
        try:    sex = r.reporter.sex
        except: pass
        try:    education_level = r.reporter.education_level
        except: pass
        try:    date_of_birth = "%d/%d/%d" % (r.reporter.date_of_birth.day, r.reporter.date_of_birth.month, r.reporter.date_of_birth.year )
        except: pass
        try:    join_date = "%d/%d/%d" % (r.reporter.join_date.day, r.reporter.join_date.month, r.reporter.join_date.year)
        except: pass
        try:    national_id = r.reporter.national_id
        except: pass
        try:    telephone_moh = r.reporter.telephone_moh
        except: pass
        try:    village = r.reporter.village.name
        except: pass
        try:    cell = r.reporter.cell.name
        except: pass
        try:    sector = r.reporter.sector.name
        except: pass
        try:    district = r.reporter.district.name
        except: pass
        try:    health_centre = r.reporter.health_centre.name
        except: pass
        try:    referral_hospital = r.reporter.referral_hospital.name
        except: pass

        sheet  = create_content(sheet, row, [surname, given_name, role, sex, \
                                                education_level, date_of_birth , join_date, national_id,\
                                                 telephone_moh, village, cell, sector,\
                                                 health_centre, referral_hospital, district])

        row = row + 1

    response = HttpResponse(mimetype = "application/ms-excel")
    response['Content-Disposition'] = 'attachment; filename = reporters.xls'
    workbook.save(response)
    return response



def excel_supervisors(chws):
    workbook = create_workbook()
    sheet = create_worksheet(workbook, "reporters")

    sheet = create_heads(sheet, ['AMAZINA','ITARIKI Y\'AMAVUKO(DD/MM/AAAA)','EMAIL','NUMERO Y\'INDANGAMUNTU', 'NUMERO YA TELEPHONE YAHAWE NA MNISANTE', 'UMUDUGUDU',\
                                 'AKAGARI', 'SECTEUR', 'CENTRE DE SANTE(Ivuriro)', 'HOPITAL(Ibitaro)', 'DISTRICT(Akarere)'])
    row   = 1

    for r in chws:

        surname = date_of_birth = email = national_id = telephone_moh = \
                 village = cell = sector = district = health_centre = referral_hospital = ""

        try:    surname = r.names
        except: pass
        try:    date_of_birth = "%d/%d/%d" % (r.dob.day, r.dob.month, r.dob.year )
        except: pass
        try:    email = r.email
        except: pass
        try:    national_id = r.national_id
        except: pass
        try:    telephone_moh = r.telephone_moh
        except: pass
        try:    village = r.village.name
        except: pass
        try:    cell = r.cell.name
        except: pass
        try:    sector = r.sector.name
        except: pass
        try:    district = r.district.name
        except: pass
        try:    health_centre = r.health_centre.name
        except: pass
        try:    referral_hospital = r.referral_hospital.name
        except: pass

        sheet  = create_content(sheet, row, [surname, date_of_birth , email, national_id,\
                                                 telephone_moh, village, cell, sector,\
                                                 health_centre, referral_hospital, district])

        row = row + 1

    response = HttpResponse(mimetype = "application/ms-excel")
    response['Content-Disposition'] = 'attachment; filename = reporters.xls'
    workbook.save(response)
    return response

