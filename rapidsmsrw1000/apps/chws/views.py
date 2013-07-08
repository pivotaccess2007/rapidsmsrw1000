#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from rapidsmsrw1000.apps.chws.models import *
from rapidsmsrw1000.apps.utils import *
from rapidsmsrw1000.apps.smser import *
from xlrd import open_workbook, cellname, XL_CELL_NUMBER, XLRDError
from django.template import RequestContext

#############
#from rapidsms.webui.utils import *
from django.template import RequestContext
from django.shortcuts import render_to_response
##############################
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django import forms ###deal with form in views
from os.path import join, isfile
from django.db.models import Count,Sum


from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseServerError, HttpResponseRedirect,Http404

from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404
from django.db import transaction, connection, IntegrityError
from django.db.models import Q
from django.contrib.auth.models import *
import time
import datetime
from django.utils import timezone
from rapidsmsrw1000.apps.chws.utils import *
from django.conf import settings

from rapidsms.router import send
from rapidsms.models import Connection,Backend


def forward (identity, text):
    try:
        if text and identity:
            try:    backend = Backend.objects.filter(name = settings.PRIMARY_BACKEND)[0]
            except: backend = Backend.objects.filter(name = 'message_tester')[0]
            #print backend
            conn = Connection(backend = backend, identity = identity)
            send(text, conn)
            return True
    except:
        #print e
        return False
        pass


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

@permission_required('chws.can_view')
def index(request):
    """Main listing."""
    request.base_template = "webapp/layout.html"
    prv = Province.objects.all().order_by("-id")

    paginator = Paginator(prv, 2)

    try: page = int(request.GET.get("page", '1'))
    except ValueError: page = 1

    try:
        prv = paginator.page(page)
    except (InvalidPage, EmptyPage):
        prv = paginator.page(paginator.num_pages)


    return render_to_response("chws/province.html", dict(prvs=prv, user=request.user), context_instance=RequestContext(request))



	
@permission_required('chws.can_view')
def chwreg(request):
    """CHW reg"""
    request.base_template = "webapp/layout.html"
    prvs = dsts = hcs = hps = scs = clls = vlls = None
    e = ""
    prvs = default_province(request)#;print prvs
    uloc = get_user_location(request)
    try:
        if uloc.health_centre or uloc.district:
            hcs = default_location(request)
            dsts = default_district(request)
            scs = Sector.objects.filter(district__in = dsts).order_by('-name')        
        if request.REQUEST.has_key('province'):    dsts = default_district(request).filter(province__id = int(request.REQUEST['province']))
        if request.REQUEST.has_key('district'):
            hcs = default_location(request).filter(district__id = int(request.REQUEST['district']))
            scs = Sector.objects.filter(district__id = int(request.REQUEST['district'])).order_by('-name')
            hps = Hospital.objects.filter(district__id = int(request.REQUEST['district'])).order_by('-name')
        if request.REQUEST.has_key('sector'):
            clls = Cell.objects.filter(sector__id = int(request.REQUEST['sector'])).order_by('-name')
            scs = scs.extra(select = {'selected':'id = %d' % (int(request.REQUEST['sector']),)})
        if request.REQUEST.has_key('cell'):
            vlls = Village.objects.filter(cell__id = int(request.REQUEST['cell'])).order_by('-name')
            clls = clls.extra(select = {'selected':'id = %d' % (int(request.REQUEST['cell']),)})
        if request.REQUEST.has_key('village'):
            vlls = Village.objects.filter(cell__id = int(request.REQUEST['cell'])).extra(select = {'selected':'id = %d' % (int(request.REQUEST['village']),)}).order_by('-name')
        
            #hps = Hospital.objects.filter(district__id = int(request.REQUEST['district'])).order_by('-name')    
        if request.REQUEST.has_key("nid") or request.REQUEST.has_key("telephone_moh"): 
            #print request.POST['nid'],request.POST['telephone_moh'],request.POST['surname'],request.POST['given_name'],request.POST['role'],request.POST['edu_level'],request.POST['sex'],request.POST['dob'],request.POST['dob'],request.POST['jod'],request.POST['hospital'],request.POST['location'],request.POST['district'],request.POST['province'],request.POST['sector'],request.POST['cell'],request.POST['village']
            try:
                try:    reporter, created = Reporter.objects.get_or_create( national_id = parse_alias(request.POST['nid']), telephone_moh = parse_phone_number(request.POST['telephone_moh']))
                except Exception,  e:
                    e = e
                    try:    reporter, created = Reporter.objects.get_or_create( national_id = parse_alias(request.POST['nid']))
                    except Exception, e:
                        e = e
                        try:    reporter, created = Reporter.objects.get_or_create( telephone_moh = parse_phone_number(request.POST['telephone_moh']))
                        except Exception, e:
                            e = e
                            reporter = Reporter( national_id = parse_alias(request.POST['nid']), telephone_moh = parse_phone_number(request.POST['telephone_moh']))

                reporter.national_id =  parse_alias(request.POST['nid'])
                reporter.telephone_moh =  parse_phone_number(request.POST['telephone_moh'])        
                reporter.surname         = get_name(parse_name(request.POST['surname']))
                reporter.given_name      = get_name(parse_name(request.POST['given_name']))
                reporter.role            = get_role(request.POST['role'])
                reporter.sex 	        =  get_sex(request.POST['sex'])
                reporter.education_level = get_education(request.POST['edu_level'])
                reporter.date_of_birth   =	get_date(request.POST['dob'])
                reporter.join_date		=   get_date(request.POST['jod'])
                reporter.district		=   District.objects.get( pk = int(request.POST['district']))
                reporter.nation			=   reporter.district.nation
                reporter.province		=   reporter.district.province
                reporter.health_centre	=   HealthCentre.objects.get(pk = int(request.POST['location']))
                reporter.sector			=   Sector.objects.get(pk = int(request.POST['sector']))
                
                reporter.referral_hospital=	Hospital.objects.get(pk = int(request.POST['hospital']))
                
                reporter.cell			=	Cell.objects.get(pk = int(request.POST['cell']))
                reporter.village		=   Village.objects.get(pk = int(request.POST['village']))
                reporter.updated		= timezone.localtime(timezone.now())
                reporter.language       = reporter.language_kinyarwanda
                reporter.save()

                confirm, created = RegistrationConfirmation.objects.get_or_create(reporter = reporter)
                confirm.save()
                contact, created = Contact.objects.get_or_create(name = reporter.national_id)
                contact.language = reporter.language#; print settings.PRIMARY_BACKEND
                backend = Backend.objects.filter(name = settings.PRIMARY_BACKEND)[0]
                connection, created = Connection.objects.get_or_create(identity = reporter.telephone_moh, backend = backend)
                connection.contact = contact
                connection.backend = backend
                contact.save()
                connection.save() 
                try:    Smser().send_message_via_kannel(reporter.telephone_moh, "Muraho! Minisiteri y'ubuzima iragusaba niba uri umujyanama w'ubuzima kohereza akajambo NDEMEYE wemeze ko uri umujyanama w'ubuzima.")
                except Exception, e:
                    e = "Message to start not sent, you can send it manually. Use Group Messages."
                    pass
                chw = reporter
                e =  "SURNAME: %s, " % chw.surname + "GIVEN NAME: %s, " %chw.given_name + "ROLE: %s, " %chw.role + "SEX: %s, " %chw.sex + "EDUCATIONAL LEVEL: %s, " %chw.education_level + "DATE OF BIRTH: %s, " %chw.date_of_birth + "JOINING DATE: %s, " %chw.join_date + "NATIONAL ID: %s, " %chw.national_id + "TELEPHONE: %s, " %chw.telephone_moh + "VILLAGE: %s, " %chw.village + "CELL: %s, " %chw.cell + "SECTOR: %s, " %chw.sector + "HEALTH CENTRE: %s, " %chw.health_centre + "REFERRAL HOSPITAL: %s, " %chw.referral_hospital + "DISTRICT: %s, " %chw.district + "PROVINCE: %s, " %chw.province + "NATION: %s, " %chw.nation + "CREATED: %s, " %chw.created + "UPDATED: %s, " %chw.updated + "LANGUAGE: %s, " %chw.language+ "Connection: %s, " %chw.connection() + "Contact: %s" %chw.contact()

            except Exception, e:
                e = e
                pass
    except Exception, e:
        e = e        
        pass    
    ##print e
    return render_to_response("chws/chwreg.html", dict(dsts = dsts, error = e, hcs = hcs, hps = hps, prvs = prvs, scs = scs, clls = clls, vlls = vlls,\
                                 user=request.user), context_instance=RequestContext(request))    


@permission_required('chws.can_view')
def group_messages(request):
    """Messaging Feature."""
    request.base_template = "webapp/layout.html"
    if get_user_location(request).user.username != 'gaju':        
        return render_to_response("ubuzima/404.html",{'error':"YOU ARE NOT ALLOWED TO SEND GROUP MESSAGES. PLEASE CONTACT ERIC GAJU"}, context_instance=RequestContext(request))
    hc = dst = None
    sent = []
    reps = Reporter.objects.all().order_by("-id")
    try:
        group = request.GET['group']
        if group == 'SUP':
            reps = Supervisor.objects.all()
        else:
            group = Report.objects.filter(name__icontains = group)[0]
            reps = reps.filter(role = group)
    except: pass

    prvs = Province.objects.all()
    try:
        province = int(request.GET['province'])

        if not province:
            pass
        else:
            reps = reps.filter( province__id = province).order_by("-id")
            prvs = Province.objects.all().extra(select = {'selected':'id = %d' % (province,)}).order_by('name')
            dst      =  District.objects.filter(province__id = province).order_by('name')

            try:
                district = int(request.GET['district'])
                if district:
                    reps = reps.filter(district__id = district).order_by("-id")
                    dst      =  District.objects.filter(province__id = province).extra(select = {'selected':'id = %d' % (district,)}).order_by('-id')
                    hc      =  HealthCentre.objects.filter(district__id = district).order_by('name')
                    try:
                        health_centre = int(request.GET['facility'])
                        if hc:
                            reps = reps.filter(health_centre__id = health_centre).order_by("-id")
                            hc      =  HealthCentre.objects.filter(district__id = \
                                                             district).extra(select = {'selected':'id = %d' % (health_centre,)}).order_by('-id')
                        else:
                            pass
                    except:
                        pass
                else:
                    pass
            except:
                pass

    except: pass

    if request.REQUEST.has_key('excel'):
        return excel_regs_confirms(RegistrationConfirmation.objects.filter( reporter__in = reps).order_by("-id"))
    else:
        try:

            if request.GET['send'] == 'SEND':
                text = request.GET['text']

                for r in reps:
                    try:
                        telephone = r.telephone_moh
                        forward(telephone, text)
                        sent.append(telephone)
                    except:
                        try:
                            telephone = r.telephone
                            Smser().send_message_via_kannel(telephone,text)#forward(telephone, text)
                        except: continue#pass
        except:
            pass
        paginator = Paginator(reps, 20)

        try: page = int(request.GET.get("page", '1'))
        except ValueError: page = 1

        try:
            reps = paginator.page(page)
        except (InvalidPage, EmptyPage):
            reps = paginator.page(paginator.num_pages)
        return render_to_response("chws/messaging.html", dict(reps = reps, sent = sent, dsts = dst, hcs = hc, prvs = prvs, user=request.user), context_instance=RequestContext(request))

@permission_required('chws.can_view')
def errors(request, ref):
    """Errors listing."""
    request.base_template = "webapp/layout.html"
    errors = Error.objects.filter(upload_ref = ref).order_by("-id")

    paginator = Paginator(errors, 20)

    try: page = int(request.GET.get("page", '1'))
    except ValueError: page = 1

    try:
        errors = paginator.page(page)
    except (InvalidPage, EmptyPage):
        errors = paginator.page(paginator.num_pages)


    return render_to_response("chws/errors.html", dict(errors=errors, user=request.user), context_instance=RequestContext(request))

@permission_required('chws.can_view')
def warnings(request, ref):
    """Errors listing."""
    request.base_template = "webapp/layout.html"
    warnings = Warn.objects.filter(upload_ref = ref).order_by("-id")

    paginator = Paginator(warnings, 20)

    try: page = int(request.GET.get("page", '1'))
    except ValueError: page = 1

    try:
        warnings = paginator.page(page)
    except (InvalidPage, EmptyPage):
        warnings = paginator.page(paginator.num_pages)


    return render_to_response("chws/warnings.html", dict(warnings=warnings, user=request.user), context_instance=RequestContext(request))

@permission_required('chws.can_view')
def view_uploads(request):
    request.base_template = "webapp/layout.html"
    hc = dst = reporters = sup = None
    prvs = Province.objects.all()
    #uploads = Error.objects.values('upload_ref').distinct('upload_ref')
    uploads = set()
    for obj in Error.objects.all():   uploads.add(obj.upload_ref)

    confirms = RegistrationConfirmation.objects.filter(responded = True, answer = True)
    pendings = RegistrationConfirmation.objects.filter(responded = False, answer = False)
    regs = RegistrationConfirmation.objects.all()
    reporters = Reporter.objects.all().values('role__id','role__name').annotate(total=Count('id')).order_by('role__name')
    sup = Supervisor.objects.all()
    try:
        province = int(request.GET['province'])

        if not province:
            pass
        else:
            uploads = set()
            for obj in Error.objects.filter(district__province__id = province):   uploads.add(obj.upload_ref)
            reporters = Reporter.objects.filter(province__id = province).values('role__id','role__name').annotate(total=Count('id')).order_by('role__name')
            sup = Supervisor.objects.filter(province__id = province)
            regs = RegistrationConfirmation.objects.filter( reporter__province__id = province).order_by("-id")
            confirms = RegistrationConfirmation.objects.filter( reporter__province__id = province, responded = True, answer = True).order_by("-id")
            pendings = RegistrationConfirmation.objects.filter( reporter__province__id = province, responded = False, answer = False).order_by("-id")
            prvs = Province.objects.all().extra(select = {'selected':'id = %d' % (province,)}).order_by('name')
            dst      =  District.objects.filter(province__id = province).order_by('name')

            try:
                district = int(request.GET['district'])
                if district:
                    uploads = set()
                    for obj in Error.objects.filter(district__id = district):   uploads.add(obj.upload_ref)
                    reporters = Reporter.objects.filter(district__id = district).values('role__id','role__name').annotate(total=Count('id')).order_by('role__name')
                    sup = Supervisor.objects.filter(district__id = district)
                    regs = RegistrationConfirmation.objects.filter( reporter__district__id = district ).order_by("-id")
                    confirms =  RegistrationConfirmation.objects.filter(reporter__district__id = district, responded = True, answer = True).order_by("-id")
                    pendings =  RegistrationConfirmation.objects.filter(reporter__district__id = district, responded = False, answer = False).order_by("-id")
                    dst      =  District.objects.filter(province__id = province).extra(select = {'selected':'id = %d' % (district,)}).order_by('-id')
                    hc      =  HealthCentre.objects.filter(district__id = district).order_by('name')
                    try:
                        health_centre = int(request.GET['facility'])
                        if hc:
                            reporters = Reporter.objects.filter(health_centre__id = health_centre).values('role__id','role__name').annotate(total=\
                                        Count('id')).order_by('role__name')
                            sup = Supervisor.objects.filter(health_centre__id = health_centre)
                            regs = RegistrationConfirmation.objects.filter( reporter__health_centre__id = health_centre ).order_by("-id")
                            confirms = RegistrationConfirmation.objects.filter(reporter__health_centre__id = health_centre, \
                                                                                responded = True, answer = True).order_by("-id")
                            pendings = RegistrationConfirmation.objects.filter(reporter__health_centre__id = health_centre, \
                                                                                responded = False, answer = False).order_by("-id")
                            hc      =  HealthCentre.objects.filter(district__id = \
                                                             district).extra(select = {'selected':'id = %d' % (health_centre,)}).order_by('-id')
                        else:
                            pass
                    except:
                        pass
                else:
                    pass
            except:
                pass

    except: pass
    errors = [Error.objects.filter(upload_ref = s)[0] for s in uploads]
    if request.REQUEST.has_key('excel'):
        return excel_regs_confirms(pendings)
    else:

        paginator = Paginator(errors, 10)

        try: page = int(request.GET.get("page", '1'))
        except ValueError: page = 1

        try:
            errors = paginator.page(page)
        except (InvalidPage, EmptyPage):
            errors = paginator.page(paginator.num_pages)


        return render_to_response("chws/uploads.html", dict( errors=errors,reporters = reporters , sup = sup, regs = regs, confirms = confirms, pendings = pendings, dsts = dst, hcs = hc, prvs = prvs, user=request.user), context_instance=RequestContext(request))

@permission_required('chws.can_view')
def view_pendings(request):
    """Pending listing."""
    request.base_template = "webapp/layout.html"
    hc = dst = None
    pendings = RegistrationConfirmation.objects.filter(responded = False, answer = False).order_by("-id")
    prvs = Province.objects.all()
    try:
        province = int(request.GET['province'])

        if not province:
            pass
        else:
            pendings = RegistrationConfirmation.objects.filter( reporter__province__id = province, responded = False, answer = False).order_by("-id")
            prvs = Province.objects.all().extra(select = {'selected':'id = %d' % (province,)}).order_by('name')
            dst      =  District.objects.filter(province__id = province).order_by('name')

            try:
                district = int(request.GET['district'])
                if district:
                    pendings =  RegistrationConfirmation.objects.filter(reporter__district__id = district, responded = False, answer = False).order_by("-id")
                    dst      =  District.objects.filter(province__id = province).extra(select = {'selected':'id = %d' % (district,)}).order_by('-id')
                    hc      =  HealthCentre.objects.filter(district__id = district).order_by('name')
                    try:
                        health_centre = int(request.GET['facility'])
                        if hc:
                            pendings = RegistrationConfirmation.objects.filter(reporter__health_centre__id = health_centre, \
                                                                                responded = False, answer = False).order_by("-id")
                            hc      =  HealthCentre.objects.filter(district__id = \
                                                             district).extra(select = {'selected':'id = %d' % (health_centre,)}).order_by('-id')
                        else:
                            pass
                    except:
                        pass
                else:
                    pass
            except:
                pass

    except: pass


    if request.REQUEST.has_key('excel'):
        return excel_regs_confirms(pendings)
    else:

        paginator = Paginator(pendings, 20)

        try: page = int(request.GET.get("page", '1'))
        except ValueError: page = 1

        try:
            pendings = paginator.page(page)
        except (InvalidPage, EmptyPage):
            pendings = paginator.page(paginator.num_pages)


        return render_to_response("chws/pendings.html", dict(pendings = pendings, dsts = dst, hcs = hc, prvs = prvs, user=request.user), context_instance=RequestContext(request))

@permission_required('chws.can_view')
def view_confirms(request):
    """confirms listing."""
    request.base_template = "webapp/layout.html"
    hc = dst = None
    confirms = RegistrationConfirmation.objects.filter(responded = True, answer = True).order_by("-id")
    prvs = Province.objects.all()
    try:
        province = int(request.GET['province'])

        if not province:
            pass
        else:
            confirms = RegistrationConfirmation.objects.filter( reporter__province__id = province, responded = True, answer = True).order_by("-id")
            prvs = Province.objects.all().extra(select = {'selected':'id = %d' % (province,)}).order_by('name')
            dst      =  District.objects.filter(province__id = province).order_by('name')

            try:
                district = int(request.GET['district'])
                if district:
                    confirms =  RegistrationConfirmation.objects.filter(reporter__district__id = district, responded = True, answer = True).order_by("-id")
                    dst      =  District.objects.filter(province__id = province).extra(select = {'selected':'id = %d' % (district,)}).order_by('-id')
                    hc      =  HealthCentre.objects.filter(district__id = district).order_by('name')
                    try:
                        health_centre = int(request.GET['facility'])
                        if hc:
                            confirms = RegistrationConfirmation.objects.filter(reporter__health_centre__id = health_centre, \
                                                                                responded = True, answer = True).order_by("-id")
                            hc      =  HealthCentre.objects.filter(district__id = \
                                                             district).extra(select = {'selected':'id = %d' % (health_centre,)}).order_by('-id')
                        else:
                            pass
                    except:
                        pass
                else:
                    pass
            except:
                pass

    except: pass

    if request.REQUEST.has_key('excel'):
        return excel_regs_confirms(confirms)
    else:
        paginator = Paginator(confirms, 20)

        try: page = int(request.GET.get("page", '1'))
        except ValueError: page = 1

        try:
            confirms = paginator.page(page)
        except (InvalidPage, EmptyPage):
            confirms = paginator.page(paginator.num_pages)
        return render_to_response("chws/confirms.html", dict(confirms = confirms, dsts = dst, hcs = hc, prvs = prvs, user=request.user), context_instance=RequestContext(request))

@permission_required('chws.can_view')
def import_reporters_from_excell(req):
    req.base_template = "webapp/layout.html"
    try:

        err,errornum, error_list, warnings,upload_ref = "", 0, None, None,None
        if req.method == 'POST':
            form = UploadImportFileForm(req.POST, req.FILES)
            if form.is_valid():
                file_to_import = process_import_file(form.cleaned_data['import_file'], req.session)

                filepath = join('/tmp/', file_to_import)
                if not isfile(filepath):
                    raise NameError, "%s is not a valid filename" % file_to_import
                book = open_workbook(filepath)

                sheet = book.sheet_by_name('reporters')
                district = form.cleaned_data['import_district']

                upload_ref = "%s_%s" % (district.name, get_time_string(time.localtime()))

                r =w = 0

                for row_index in range(sheet.nrows):

                        row_num     = row_index
                        if row_num < 1 : continue

                        try:

                            reporter = initialize_reporter(row_num, sheet)

                            chw, created = Reporter.objects.get_or_create(national_id = reporter.national_id, telephone_moh = reporter.telephone_moh)
                            chw = update_reporter(row_num, sheet, chw)
                            chw.save()
                            print r, chw.surname, chw.given_name, chw.role, chw.sex, chw.education_level, chw.date_of_birth, chw.join_date, chw.national_id, chw.telephone_moh, chw.village, chw.cell, chw.sector, chw.health_centre, chw.referral_hospital, chw.district, chw.province, chw.nation, chw.created, chw.updated, chw.language
                            if not reporter.national_id:
                                ikosa = set_error("Row: %d ===>>> Error: %s" % (int(row_num+1),"Wrong National ID"), \
                                                                    req, reporter.district, row_num, sheet, upload_ref,e)
                                continue#print ikosa

                            if not reporter.telephone_moh:
                                ikosa = set_error("Row: %d ===>>> Error: %s" % ((row_num+1),"Wrong Telephone Number"), \
                                                                    req, reporter.district, row_num, sheet, upload_ref,e)
                                continue#print ikosa

                            try:
                                confirm, created = RegistrationConfirmation.objects.get_or_create(reporter = chw)
                                confirm.save()

                                for c in reporter.__dict__:
                                        if c[0] == "_":  pass
                                        else:
                                            if reporter.__dict__[c] == '' or  reporter.__dict__[c] == None:
                                                ikosa = set_warn("Row: %d ===>>> Warning: %s MISSING OR WRONG" % (int(row_num+1), c), \
                                                                req, reporter.district, row_num, sheet, upload_ref)

                                #r = r + 1
                                #print r, chw.surname, chw.given_name, chw.role, chw.sex, chw.education_level, chw.date_of_birth, chw.join_date, chw.national_id, chw.telephone_moh, chw.village, chw.cell, chw.sector, chw.health_centre, chw.referral_hospital, chw.district, chw.province, chw.nation, chw.created, chw.updated, chw.language
                            except Exception, e:
                                print e, row_num
                                pass
                            error_list, warnings = Error.objects.filter( upload_ref = upload_ref), Warn.objects.filter( upload_ref = upload_ref)
                        except Exception,e:
                                errornum+=1
                                print e
                                continue

        else:
                form = UploadImportFileForm()
        if errornum >= 1: err="Error: %s"%e

        return render_to_response('chws/import.html', {'form': form,'error':error_list, 'warn':warnings, 'ref':upload_ref}, context_instance=RequestContext(req))

    except Exception,e:
        return render_to_response("chws/404.html",{'error':e}, context_instance=RequestContext(req))


def process_import_file(import_file, session):
    """
    Open the uploaded file and save it to the temp file location specified
    in BATCH_IMPORT_TEMPFILE_LOCATION, adding the current session key t
    the file name. Then return the file name so it can be stored in the
    session for the current user.

    **Required arguments**

    ``import_file``
        The uploaded file object.

    ``session``
        The session object for the current user.

    ** Returns**

    ``save_file_name``
        The name of the file saved to the temp location.


    """
    import_file_name = import_file.name
    session_key = session.session_key
    save_file_name = session_key + import_file_name
    destination = open(join('/tmp/', save_file_name), 'wb+')
    for chunk in import_file.chunks():
        destination.write(chunk)
    destination.close()
    return save_file_name



def parse_alias(alias):
    try:
        if type(alias)!=str:
            alias=str(int(alias))
        elif type(alias)==str:
            alias=alias.replace(" ","")
    except Exception:
        try:
            alias=alias.replace(" ","")
        except: return False

    return alias if len(alias) == 16 else False


def parse_phone_number(number):

    number = number
    try:
        number = str(int(float(number)))
    except:
        try:
            number = str(int(number))
        except:
            try:
                number = str(number)
            except:
                    return False
    number = number.replace(" ", "")
    try:
        if type(number)!=str:
            number=str(int(number))
        if number[:3]=="+25" and len(number[3:])==10:
            number=number
        elif number[:3]=="250" and len(number[3:])==9:
            number="+"+number
        elif number[:3]=="078" and len(number[3:])==7:
            number="+25"+number
        elif number[:2]=="78" and len(number[2:])==7:
            number="+250"+number
        return number
    except:
            return False


def parse_name(n):
    try:
        n=n.split(" ")
        if len(n) > 1:
            return n[0],n[1]
        elif len(n) == 1:
            return n[0]," "
        else: return " "," "
    except Exception,e:
        return " "


def chws_list_template():

	import xlwt
	book = xlwt.Workbook(encoding="utf-8")
	chws_sheet = book.add_sheet("CHWs")
	heading = ["Izina ry'umuryango", "Andi mazina",	"Icyo akora(Binome, ASM)",	"Igitsina(F:Gore,M:Gabo)",
			"Amashuri yize(P:Primaire, S:Secondaire, U:University, N:Ntabwo yize)",	"Itariki y'amavuko(DD/MM/AAAA)",
			"Itariki y'ubujyanama(AAAA:Umwaka)",	"Numero y'indangamuntu", "Numero ya telefone yahawena Minisante",
			"Umudugudu",	"Akagari",	"Secteur",	"Centre de sante(Ivuriro)",	"Hopital(Ibitaro)",	"District(Akarere)"]
	cell_index = 0
	for h in heading:

			chws_sheet.write(0, cell_index, h)
			cell_index = cell_index + 1


	book.save("/tmp/CHWs_LIST_TEMPLATE.xls") # heading row

	return True

def download_chws_list_template(req, directory = "/tmp"):
    response = HttpResponse(mimetype='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=CHWs_LIST_TEMPLATE.xls'

    return response

def downloadLogs(req, dir):
    response = HttpResponse(mimetype='application/x-gzip')
    response['Content-Disposition'] = 'attachment; filename=download.tar.gz'
    tarred = tarfile.open(fileobj=response, mode='w:gz')
    tarred.add(dir)
    tarred.close()

    return response

class UploadImportFileForm(forms.Form):
	import_district = forms.ModelChoiceField(queryset = District.objects.all(), required = False, label = "Select District:")
	import_file = forms.FileField(label='Select your XLS file:')

def get_name(name):
    try:
        name    = "%s %s" % (name[0],name[1])
        return name
    except:
            name = name[0]
            return name

def get_role(role):
    
    try:
        if "asm" in role.lower() :  role = Role.objects.get( code ='asm')
        elif "a.s.m" in role.lower():   role = Role.objects.get( code ='asm')
        elif "asc" in role.lower():   role = Role.objects.get( code ='asm')
        elif "binome" in role.lower() : role = Role.objects.get( code ='binome')
        elif "bin" in role.lower() : role = Role.objects.get( code ='binome')
        return role
    except:
        return Role.objects.get( code ='asm')

def get_sex (sex):
    try:

        if 'f' in sex.lower():  sex = Reporter.sex_female
        elif 'm' in sex.lower():  sex = Reporter.sex_male
        elif 'gore' in sex.lower():  sex = Reporter.sex_female
        elif 'gabo' in sex.lower():  sex = Reporter.sex_male
        else:   sex = Reporter.sex_female
        return sex
    except:
        return  Reporter.sex_female

def get_education(education_level):

    if "p" in education_level.lower(): education_level = Reporter.education_primaire
    elif "s" in education_level.lower(): education_level = Reporter.education_secondaire
    elif "u" in education_level.lower(): education_level = Reporter.education_universite
    else:   education_level = Reporter.education_ntayo
    return education_level

def get_date(date_of_birth):

    try:
        x       = date_of_birth.split("/")
        if len(x) == 3 :    date_of_birth       = datetime.date(int(x[2]),int(x[1]),int(x[0]))
        elif len(x) == 1:   date_of_birth       = datetime.date(int(x[0]),01,01)
    except:
        try:
            x = int(float(date_of_birth))
            if x: date_of_birth = datetime.date(x,01,01)
        except:   date_of_birth = datetime.date.today() - datetime.timedelta(days = 7665)
    return date_of_birth

def get_nation(name = "Rwanda"):
    try:
        return Nation.objects.get(name = name)
    except: return None

def get_district(name):
    try:
        district = District.objects.filter(name__icontains = name)
        return district[0]
    except: return None

def parse_l_r_name(name):
    try:
        return name.replace("l", "r")
    except:
        return name.replace("r", "l")


def get_sector(name, district):
    try:
        sector = Sector.objects.filter(name = name, district = district)
        return sector[0]
    except:
        sector = Sector.objects.filter(name__icontains = parse_l_r_name(name), district = district)
        if sector.exists(): return sector[0]
        else:   return None


def get_cell(name, sector):
    try:
        cell = Cell.objects.filter(name = name, sector = sector)
        return cell[0]
    except:
        cell = Cell.objects.filter(name__icontains = parse_l_r_name(name), sector = sector)
        if cell.exists(): return cell[0]
        else:   return None

def get_village(name, cell):
    try:
        village = Village.objects.filter(name = name, cell = cell)
        return village[0]
    except:
        village = Village.objects.filter(name__icontains = parse_l_r_name(name), cell = cell)
        if village.exists(): return village[0]
        else:   return None

def get_health_centre(name, district):
    try:
        hc = HealthCentre.objects.filter(name = name, district = district)
        return hc[0]
    except:
        hc = HealthCentre.objects.filter(name__icontains = parse_l_r_name(name), district = district)
        if hc.exists(): return hc[0]
        else:   return None

def get_referral_hospital(name, district):
    try:
        hosp = Hospital.objects.filter(name = name, district = district)
        return hosp[0]
    except:
        hosp = Hospital.objects.filter(name__icontains = parse_l_r_name(name), district = district)
        if hosp.exists(): return hc[0]
        else:   return None


def initialize_reporter(row, sheet):

    try:
        reporter = Reporter( national_id = parse_alias(sheet.cell(row,7).value), telephone_moh = parse_phone_number(sheet.cell(row,8).value))
        reporter.surname         = get_name(parse_name(sheet.cell(row,0).value))
        reporter.given_name      = get_name(parse_name(sheet.cell(row,1).value))
        reporter.role            = get_role(sheet.cell(row,2).value)
        reporter.sex 	        =  get_sex(sheet.cell(row,3).value)
        reporter.education_level = get_education(sheet.cell(row,4).value)
        reporter.date_of_birth   =	get_date(sheet.cell(row,5).value)
        reporter.join_date		=   get_date(sheet.cell(row,6).value)
        reporter.district		=   get_district(sheet.cell(row,14).value)
        reporter.nation			=   reporter.district.nation
        reporter.province		=   reporter.district.province
        reporter.sector			=   get_sector(sheet.cell(row,11).value, district = reporter.district)
        #print reporter.sector
        reporter.referral_hospital=	get_referral_hospital(name = sheet.cell(row,13).value, district = reporter.district)
        reporter.health_centre	=   get_health_centre(name = sheet.cell(row,12).value, district = reporter.district)
        reporter.cell			=	get_cell(name = sheet.cell(row,10).value, sector = reporter.sector)
        reporter.village		=   get_village(name = sheet.cell(row,9).value, cell = reporter.cell)
        reporter.updated		    = timezone.localtime(timezone.now())
        reporter.language        = reporter.language_kinyarwanda

    except Exception, e:    print e
    return reporter

def update_reporter(row, sheet, reporter):

    #reporter.national_id     = parse_alias(sheet.cell(row,7).value)
    #reporter.telephone_moh   = parse_phone_number(sheet.cell(row,8).value)
    reporter.surname         = get_name(parse_name(sheet.cell(row,0).value))
    reporter.given_name      = get_name(parse_name(sheet.cell(row,1).value))
    reporter.role            = get_role(sheet.cell(row,2).value)
    reporter.sex 	        =  get_sex(sheet.cell(row,3).value)
    reporter.education_level = get_education(sheet.cell(row,4).value)
    reporter.date_of_birth   =	get_date(sheet.cell(row,5).value)
    reporter.join_date		=   get_date(sheet.cell(row,6).value)
    reporter.district		=   get_district(sheet.cell(row,14).value)
    reporter.nation			=   reporter.district.nation
    reporter.province		=   reporter.district.province
    reporter.sector			=   get_sector(sheet.cell(row,11).value, district = reporter.district)
    reporter.referral_hospital=	get_referral_hospital(name = sheet.cell(row,13).value, district = reporter.district)
    reporter.health_centre	=   get_health_centre(name = sheet.cell(row,12).value, district = reporter.district)
    reporter.cell			=	get_cell(name = sheet.cell(row,10).value, sector = reporter.sector)
    reporter.village		=   get_village(name = sheet.cell(row,9).value, cell = reporter.cell)
    reporter.updated		= timezone.localtime(timezone.now())
    reporter.language       = reporter.language_kinyarwanda

    return reporter


def set_error(msg, req, district, row_num, sheet, upload_ref, e):
    try:
        er_msg = Error(row = int(row_num)+1, sheet = sheet.name, upload_ref = upload_ref, district = district, when = timezone.localtime(timezone.now()), by = req.user, error_message = msg)
        if e.message != 'Reporter matching query does not exist.': er_msg.save()
        return er_msg
    except: pass

def set_warn(msg, req, district, row_num, sheet, upload_ref):
    try:
        warn_msg = Warn(row = int(row_num)+1, sheet = sheet.name, upload_ref = upload_ref, district = district, when = timezone.localtime(timezone.now()), by = req.user, warning_message = msg)
        warn_msg.save()
        return warn_msg
    except: pass

def get_time_string(localtime): ##  localtime   = time.localtime()
		return time.strftime("%Y_%m_%d_%H_%M_%S", localtime)


####START INACTIVITY
def inactive_reporters(req, rez, group):
    reps = Reporter.objects.filter(role=group, **rez)
    pst = reporter_fresher(req)
    return reps.filter(**pst).filter(is_active=False)


def active_reporters(req, rez, group):
    reps = Reporter.objects.filter(role=group, **rez)
    pst = reporter_fresher(req);print pst,rez
    return reps.filter(**pst).filter(is_active=True)


def matching_filters(req,diced,alllocs=False):
    rez = {}
    pst = None

    try:
        if alllocs: raise KeyError
        loc = int(req.REQUEST['location'])
        rez['health_centre__id'] = loc
    except KeyError:
        try:
            rez['district__id'] = int(req.REQUEST['district'])
        except KeyError:
            try:
                rez['province__id'] = int(req.REQUEST['province'])
            except KeyError:
                pass

    return rez

@permission_required('chws.can_view')
def view_active_reporters(req,**flts):
    req.base_template = "webapp/layout.html"
    try:    group = Role.objects.get(code = req.REQUEST['group'])
    except Exception,err: return render_to_response("chws/404.html",{"error":err}, context_instance=RequestContext(req))
    filters = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    lox, lxn = 0, location_name(req)

    rez = matching_filters(req,filters)
    reporters = active_reporters(req,rez, group)
    if req.REQUEST.has_key('location') and req.REQUEST['location'] != '0':
        lox = int(req.REQUEST['location'])
        lxn = HealthCentre.objects.get(id = lox)
        lxn=lxn.name+' '+"Health Centre"+', '+lxn.district.name+' '+"District"+', '+lxn.province.name+' '

    if req.REQUEST.has_key('excel'):
        return excel_chws(reporters)
    elif req.REQUEST.has_key('csv'):
        return csv_chws(reporters, group)
    else:
        return render_to_response(
            "chws/active.html", {
            "reporters": paginated(req, active_reporters(req,rez, group)),'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),
             'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,'locationname':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1]
              }, context_instance=RequestContext(req))

@permission_required('chws.can_view')
def view_inactive_reporters(req,**flts):

    req.base_template = "webapp/layout.html"
    try:    group = Role.objects.get(code = req.REQUEST['group'])
    except Exception,err: return render_to_response("chws/404.html",{"error":err}, context_instance=RequestContext(req))
    filters = {'period':default_period(req),
             'location':default_location(req),
             'province':default_province(req),
             'district':default_district(req)}
    lox, lxn = 0, location_name(req)

    rez = matching_filters(req,filters)
    reporters = inactive_reporters(req,rez, group)
    if req.REQUEST.has_key('location') and req.REQUEST['location'] != '0':
        lox = int(req.REQUEST['location'])
        lxn = HealthCentre.objects.get(id = lox)
        lxn=lxn.name+' '+"Health Centre"+', '+lxn.district.name+' '+"District"+', '+lxn.province.name+' '

    if req.REQUEST.has_key('excel'):
        return excel_chws(reporters)
    elif req.REQUEST.has_key('csv'):
        return csv_chws(reporters, group)
    else:
        return render_to_response(
        "chws/inactive.html", {
        "reporters": paginated(req, reporters),'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),
         'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,'locationname':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1]
          }, context_instance=RequestContext(req))


@permission_required('chws.can_view')
def activity_statistics(req):

    filters = {'period':default_period(req),
                 'location':default_location(req),
                 'province':default_province(req),
                 'district':default_district(req)}
        
    rez = matching_filters(req,filters)
    pst = reporter_fresher(req)
        
    lox, lxn = 0, location_name(req)

    start = filters['period']['start']
    end = filters['period']['end']

    report_type = {}
    days = (end - start).days
    

    #messages = Message.objects.filter(direction = 'I', date__gte = start , date__lte = end).exclude(contact = None)
    reports = Report.objects.filter(created__gte = start - datetime.timedelta(days = 14), created__lte = end - datetime.timedelta(days = 14))

    #contacts_from_messages = [ s[0] for s in set(messages.values_list('contact__name')) ]
    reportes_from_reports = [ s[0] for s in set(reports.values_list('reporter__id')) ] 

    #active_reporters = Reporter.objects.filter(id__in = reportes_from_reports, national_id__in = contacts_from_messages, **rez).filter(**pst)
    #inactive_reporters = Reporter.objects.filter(**rez).filter(**pst).exclude(id__in = active_reporters.values_list('pk'))
    active_reporters = Reporter.objects.filter(id__in = reportes_from_reports, **rez).filter(**pst)
    inactive_reporters = Reporter.objects.filter(**rez).filter(**pst).exclude(id__in = active_reporters.values_list('pk'))

    xaxes = []
    if days <= 7:
        report_type = {'title':'Daily','axe':'Day'}
        xaxes  = days_between(start, end)
        tracks = chws_attendance_daily(req,rez, pst, xaxes)
    elif days > 7 :
        report_type = {'title':'Monthly','axe':'Month - Year'}
        xaxes = months_between(start, end)
        tracks = chws_attendance_monthly(req,rez, pst, xaxes)
 
    if req.REQUEST.has_key('dat') and req.REQUEST.has_key('gr'):

        tracks = tracks['reporters'][req.REQUEST['dat']]
        title = req.REQUEST['gr'].replace('_'," ").upper()

        if req.REQUEST.has_key('format'):
            if req.REQUEST['format'] == 'excel':
                return excel_chws(tracks[req.REQUEST['gr']])    
        else:

            return render_to_response(
            "chws/reporter.html", {
            "reporters": paginated(req, tracks[req.REQUEST['gr']]), 'title': title,'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'),
             'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,'locationname':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1]
              }, context_instance=RequestContext(req))
        
    return render_to_response(
        "chws/dashboard.html",
        {'reporters':  tracks['reporters'], 'tracks': SafeString(json.dumps(tracks['total'])), 'report_type': report_type, 'xaxes': [str(x) for x in xaxes],'start_date':date.strftime(filters['period']['start'], '%d.%m.%Y'), 'end_date':date.strftime(filters['period']['end'], '%d.%m.%Y'),'filters':filters,'locationname':lxn,'postqn':(req.get_full_path().split('?', 2) + [''])[1]
          }, context_instance=RequestContext(req))


def chws_attendance_monthly(req, rez, pst, months_between):

    ans = {}; total = {}; reporters = {}
    total['active_asm'] = {}
    total['active_binome'] = {}
    total['inactive_asm'] = {}
    total['inactive_binome'] = {}

    reporters ={}
    asm = Reporter.objects.filter(role__code = 'asm').filter(**rez).filter(**pst).count()    
    binome = Reporter.objects.filter(role__code = 'binome').filter(**rez).filter(**pst).count()
    
    for m in months_between:
        s = m.split('-')
        rang = calendar.monthrange(int(s[1]),int(s[0]))
        start = date(int(s[1]), int(s[0]), 1)
        end = date(int(s[1]), int(s[0]), rang[1]) #; print "START: %s , END: %s" % (start, end)
        #messages = Message.objects.filter(direction = 'I', date__gte = start - datetime.timedelta(days = 14) , date__lte = end - datetime.timedelta(days = 14)).exclude(contact = None)
        reports = Report.objects.filter(created__gte = start - datetime.timedelta(days = 14), created__lte = end - datetime.timedelta(days = 14))
        #contacts_from_messages = [ s[0] for s in set(messages.values_list('contact__name')) ]
        reportes_from_reports = [ s[0] for s in set(reports.values_list('reporter__id')) ]
        #active_reporters = Reporter.objects.filter(id__in = reportes_from_reports, national_id__in = contacts_from_messages, **rez).filter(**pst)
        #inactive_reporters = Reporter.objects.filter(**rez).filter(**pst).exclude(id__in = active_reporters.values_list('pk'))
        active_reporters = Reporter.objects.filter(id__in = reportes_from_reports, **rez).filter(**pst)
        inactive_reporters = Reporter.objects.filter(**rez).filter(**pst).exclude(id__in = active_reporters.values_list('pk'))
        

        total['active_asm'][m] =  float(active_reporters.filter(role__code = 'asm').count())*100/asm
        
        total['active_binome'][m] = float(active_reporters.filter(role__code = 'binome').count())*100/binome
        
        total['inactive_asm'][m] = float(inactive_reporters.filter(role__code = 'asm').count())*100/asm
        
        total['inactive_binome'][m] = float(inactive_reporters.filter(role__code = 'binome').count())*100/binome
       

        reporters[m] = {'active_asm': active_reporters.filter(role__code = 'asm'),
                        'active_binome':  active_reporters.filter(role__code = 'binome'),
                        'inactive_asm':  inactive_reporters.filter(role__code = 'asm'),
                         'inactive_binome':  inactive_reporters.filter(role__code = 'binome'),
                            'active_asm_percent': float(active_reporters.filter(role__code = 'asm').count())*100/asm,
                            'active_binome_percent': float(active_reporters.filter(role__code = 'binome').count())*100/binome,
                            'inactive_asm_percent': float(inactive_reporters.filter(role__code = 'asm').count())*100/asm,
                            'inactive_binome_percent': float(inactive_reporters.filter(role__code = 'binome').count())*100/binome,}

    #print rez, pst, total,reporters
    ans = {'total': total, 'reporters': reporters}

    return ans 

def chws_attendance_daily(req, rez, pst, days_b):

    ans = {}; total = {}; reporters = {}
    total['active_asm'] = {}
    total['active_binome'] = {}
    total['inactive_asm'] = {}
    total['inactive_binome'] = {}

    reporters ={}
    asm = Reporter.objects.filter(role__code = 'asm').filter(**rez).filter(**pst).count()    
    binome = Reporter.objects.filter(role__code = 'binome').filter(**rez).filter(**pst).count()    

    for day in days_b:
        d = str(day)#; print d
        start = day - datetime.timedelta(days = 14)
        end = day
        #messages = Message.objects.filter(direction = 'I', date__gte = start , date__lte = end).exclude(contact = None)
        reports = Report.objects.filter(created__gte = start, created__lte = end)
        #contacts_from_messages = [ s[0] for s in set(messages.values_list('contact__name')) ]
        reportes_from_reports = [ s[0] for s in set(reports.values_list('reporter__id')) ]
        #active_reporters = Reporter.objects.filter(id__in = reportes_from_reports, national_id__in = contacts_from_messages, **rez).filter(**pst)
        #inactive_reporters = Reporter.objects.filter(**rez).filter(**pst).exclude(id__in = active_reporters.values_list('pk'))
        
        active_reporters = Reporter.objects.filter(id__in = reportes_from_reports, **rez).filter(**pst)
        inactive_reporters = Reporter.objects.filter(**rez).filter(**pst).exclude(id__in = active_reporters.values_list('pk'))

        
        total['active_asm'][d] =  float(active_reporters.filter(role__code = 'asm').count())*100/asm
        
        total['active_binome'][d] = float(active_reporters.filter(role__code = 'binome').count())*100/binome
        
        total['inactive_asm'][d] = float(inactive_reporters.filter(role__code = 'asm').count())*100/asm
        
        total['inactive_binome'][d] = float(inactive_reporters.filter(role__code = 'binome').count())*100/binome
       

        reporters[d] = {'active_asm': active_reporters.filter(role__code = 'asm'),
                        'active_binome':  active_reporters.filter(role__code = 'binome'),
                        'inactive_asm':  inactive_reporters.filter(role__code = 'asm'),
                         'inactive_binome':  inactive_reporters.filter(role__code = 'binome'),
                            'active_asm_percent': float(active_reporters.filter(role__code = 'asm').count())*100/asm,
                            'active_binome_percent': float(active_reporters.filter(role__code = 'binome').count())*100/binome,
                            'inactive_asm_percent': float(inactive_reporters.filter(role__code = 'asm').count())*100/asm,
                            'inactive_binome_percent': float(inactive_reporters.filter(role__code = 'binome').count())*100/binome,}

    #print rez, pst, total,reporters
    ans = {'total': total, 'reporters': reporters}

    return ans

#####END OF INACTIVITY

@permission_required('chws.can_view')
def view_asm(request):
    """asm listing."""
    request.base_template = "webapp/layout.html"
    hc = dst = None

    asms = Reporter.objects.filter(role__code = 'asm').order_by("-id")
    prvs = Province.objects.all()

    try:
        province = int(request.GET['province'])

        if not province:
            pass
        else:

            asms = asms.filter( province__id = province).order_by("-id")
            prvs = Province.objects.all().extra(select = {'selected':'id = %d' % (province,)}).order_by('name')
            dst      =  District.objects.filter(province__id = province).order_by('name')

            try:
                district = int(request.GET['district'])
                if district:
                    asms =  asms.filter(district__id = district).order_by("-id")
                    dst      =  District.objects.filter(province__id = province).extra(select = {'selected':'id = %d' % (district,)}).order_by('-id')
                    hc      =  HealthCentre.objects.filter(district__id = district).order_by('name')
                    try:
                        health_centre = int(request.GET['facility'])
                        if hc:
                            asms = asms.filter(health_centre__id = health_centre).order_by("-id")
                            hc      =  HealthCentre.objects.filter(district__id = \
                                                             district).extra(select = {'selected':'id = %d' % (health_centre,)}).order_by('-id')
                        else:
                            pass
                    except:
                        pass
                else:
                    pass
            except:
                pass

    except: pass

    if request.REQUEST.has_key('excel'):
        return excel_chws(asms)
    else:
        paginator = Paginator(asms, 20)

        try: page = int(request.GET.get("page", '1'))
        except ValueError: page = 1

        try:
            asms = paginator.page(page)
        except (InvalidPage, EmptyPage):
            asms = paginator.page(paginator.num_pages)
        return render_to_response("chws/asm.html", dict(asms = asms, dsts = dst, hcs = hc, prvs = prvs, user=request.user), context_instance=RequestContext(request))


@permission_required('chws.can_view')
def view_binome(request):
    """Binome listing."""
    request.base_template = "webapp/layout.html"
    hc = dst = None

    binomes = Reporter.objects.filter(role__code = 'binome').order_by("-id")
    prvs = Province.objects.all()

    try:
        province = int(request.GET['province'])

        if not province:
            pass
        else:

            binomes = binomes.filter( province__id = province).order_by("-id")
            prvs = Province.objects.all().extra(select = {'selected':'id = %d' % (province,)}).order_by('name')
            dst      =  District.objects.filter(province__id = province).order_by('name')

            try:
                district = int(request.GET['district'])
                if district:
                    binomes =  binomes.filter(district__id = district).order_by("-id")
                    dst      =  District.objects.filter(province__id = province).extra(select = {'selected':'id = %d' % (district,)}).order_by('-id')
                    hc      =  HealthCentre.objects.filter(district__id = district).order_by('name')
                    try:
                        health_centre = int(request.GET['facility'])
                        if hc:
                            binomes = binomes.filter(health_centre__id = health_centre).order_by("-id")
                            hc      =  HealthCentre.objects.filter(district__id = \
                                                             district).extra(select = {'selected':'id = %d' % (health_centre,)}).order_by('-id')
                        else:
                            pass
                    except:
                        pass
                else:
                    pass
            except:
                pass

    except: pass

    if request.REQUEST.has_key('excel'):
        return excel_chws(binomes)
    else:
        paginator = Paginator(binomes, 20)

        try: page = int(request.GET.get("page", '1'))
        except ValueError: page = 1

        try:
            binomes = paginator.page(page)
        except (InvalidPage, EmptyPage):
            binomes = paginator.page(paginator.num_pages)
        return render_to_response("chws/binome.html", dict(binomes = binomes, dsts = dst, hcs = hc, prvs = prvs, user=request.user), context_instance=RequestContext(request))

@permission_required('chws.can_view')
def view_supervisor(request):
    """Supervisor listing."""
    request.base_template = "webapp/layout.html"
    hc = dst = None

    supervisors = Supervisor.objects.all().order_by("-id")
    prvs = Province.objects.all()

    try:
        province = int(request.GET['province'])

        if not province:
            pass
        else:

            supervisors = supervisors.filter( province__id = province).order_by("-id")
            prvs = Province.objects.all().extra(select = {'selected':'id = %d' % (province,)}).order_by('name')
            dst      =  District.objects.filter(province__id = province).order_by('name')

            try:
                district = int(request.GET['district'])
                if district:
                    supervisors =  supervisors.filter(district__id = district).order_by("-id")
                    dst      =  District.objects.filter(province__id = province).extra(select = {'selected':'id = %d' % (district,)}).order_by('-id')
                    hc      =  HealthCentre.objects.filter(district__id = district).order_by('name')
                    try:
                        health_centre = int(request.GET['facility'])
                        if hc:
                            supervisors = supervisors.filter(health_centre__id = health_centre).order_by("-id")
                            hc      =  HealthCentre.objects.filter(district__id = \
                                                             district).extra(select = {'selected':'id = %d' % (health_centre,)}).order_by('-id')
                        else:
                            pass
                    except:
                        pass
                else:
                    pass
            except:
                pass

    except: pass

    if request.REQUEST.has_key('excel'):
        return excel_supervisors(supervisors)
    else:
        paginator = Paginator(supervisors, 20)

        try: page = int(request.GET.get("page", '1'))
        except ValueError: page = 1

        try:
            supervisors = paginator.page(page)
        except (InvalidPage, EmptyPage):
            supervisors = paginator.page(paginator.num_pages)
        return render_to_response("chws/supervisor.html", dict(supervisors = supervisors, dsts = dst, hcs = hc, prvs = prvs, user=request.user), context_instance=RequestContext(request))

@permission_required('chws.can_view')
def view_datamanager(request):
    """Data Managers listing."""
    request.base_template = "webapp/layout.html"
    hc = dst = None

    datamangers = DataManager.objects.all().order_by("-id")
    prvs = Province.objects.all()

    try:
        province = int(request.GET['province'])

        if not province:
            pass
        else:

            datamangers = datamangers.filter( province__id = province).order_by("-id")
            prvs = Province.objects.all().extra(select = {'selected':'id = %d' % (province,)}).order_by('name')
            dst      =  District.objects.filter(province__id = province).order_by('name')

            try:
                district = int(request.GET['district'])
                if district:
                    datamangers =  datamangers.filter(district__id = district).order_by("-id")
                    dst      =  District.objects.filter(province__id = province).extra(select = {'selected':'id = %d' % (district,)}).order_by('-id')
                    hc      =  HealthCentre.objects.filter(district__id = district).order_by('name')
                    try:
                        health_centre = int(request.GET['facility'])
                        if hc:
                            datamangers = datamangers.filter(health_centre__id = health_centre).order_by("-id")
                            hc      =  HealthCentre.objects.filter(district__id = \
                                                             district).extra(select = {'selected':'id = %d' % (health_centre,)}).order_by('-id')
                        else:
                            pass
                    except:
                        pass
                else:
                    pass
            except:
                pass

    except: pass

    if request.REQUEST.has_key('excel'):
        return excel_supervisors(datamangers)
    else:
        paginator = Paginator(datamangers, 20)

        try: page = int(request.GET.get("page", '1'))
        except ValueError: page = 1

        try:
            datamangers = paginator.page(page)
        except (InvalidPage, EmptyPage):
            datamangers = paginator.page(paginator.num_pages)
        return render_to_response("chws/datamanager.html", dict(datamangers = datamangers, dsts = dst, hcs = hc, prvs = prvs, user=request.user), context_instance=RequestContext(request))

@permission_required('chws.can_view')
def view_facilitystaff(request):
    """Facility Staff listing."""
    request.base_template = "webapp/layout.html"
    hc = dst = None

    facilitystaff = FacilityStaff.objects.all().order_by("-id")
    prvs = Province.objects.all()

    try:
        province = int(request.GET['province'])

        if not province:
            pass
        else:

            facilitystaff = facilitystaff.filter( province__id = province).order_by("-id")
            prvs = Province.objects.all().extra(select = {'selected':'id = %d' % (province,)}).order_by('name')
            dst      =  District.objects.filter(province__id = province).order_by('name')

            try:
                district = int(request.GET['district'])
                if district:
                    facilitystaff =  facilitystaff.filter(district__id = district).order_by("-id")
                    dst      =  District.objects.filter(province__id = province).extra(select = {'selected':'id = %d' % (district,)}).order_by('-id')
                    hc      =  HealthCentre.objects.filter(district__id = district).order_by('name')
                    try:
                        health_centre = int(request.GET['facility'])
                        if hc:
                            facilitystaff = facilitystaff.filter(health_centre__id = health_centre).order_by("-id")
                            hc      =  HealthCentre.objects.filter(district__id = \
                                                             district).extra(select = {'selected':'id = %d' % (health_centre,)}).order_by('-id')
                        else:
                            pass
                    except:
                        pass
                else:
                    pass
            except:
                pass

    except: pass

    if request.REQUEST.has_key('excel'):
        return excel_supervisors(facilitystaff)
    else:
        paginator = Paginator(facilitystaff, 20)

        try: page = int(request.GET.get("page", '1'))
        except ValueError: page = 1

        try:
            facilitystaff = paginator.page(page)
        except (InvalidPage, EmptyPage):
            facilitystaff = paginator.page(paginator.num_pages)
        return render_to_response("chws/facilitystaff.html", dict(facilitystaff = facilitystaff, dsts = dst, hcs = hc, prvs = prvs, user=request.user), context_instance=RequestContext(request))
