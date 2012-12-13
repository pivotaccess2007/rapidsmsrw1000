#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsmsrw1000.apps.chws.models import *
from xlrd import open_workbook ,cellname,XL_CELL_NUMBER,XLRDError
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
import csv

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
from rapidsmsrw1000.apps.ubuzima.utils import *
from rapidsmsrw1000.apps.reporters import models as old_registry


@permission_required('chws.can_view')
@require_GET
@require_http_methods(["GET"])
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
@require_GET
@require_http_methods(["GET"])
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

@require_GET
@require_http_methods(["GET"])
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
    paginator = Paginator(errors, 10)
    
    try: page = int(request.GET.get("page", '1'))
    except ValueError: page = 1

    try:
        errors = paginator.page(page)
    except (InvalidPage, EmptyPage):
        errors = paginator.page(paginator.num_pages)

    
    return render_to_response("chws/uploads.html", dict( errors=errors,reporters = reporters , sup = sup, regs = regs, confirms = confirms, pendings = pendings, dsts = dst, hcs = hc, prvs = prvs, user=request.user), context_instance=RequestContext(request))

@permission_required('chws.can_view')
@require_GET
@require_http_methods(["GET"])
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
@require_GET
@require_http_methods(["GET"])
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
                            #chw.save()
                            #print r, chw.surname, chw.given_name, chw.role, chw.sex, chw.education_level, chw.date_of_birth, chw.join_date, chw.national_id, chw.telephone_moh, chw.village, chw.cell, chw.sector, chw.health_centre, chw.referral_hospital, chw.district, chw.province, chw.nation, chw.created, chw.updated, chw.language
                            if not reporter.national_id:
                                ikosa = set_error("Row: %d ===>>> Error: %s" % (int(row_num+1),"Wrong National ID"), \
                                                                    req, reporter.district, row_num, sheet, upload_ref,e)
                                continue#print ikosa

                            if not reporter.telephone_moh:
                                ikosa = set_error("Row: %d ===>>> Error: %s" % ((row_num+1),"Wrong Telephone Number"), \
                                                                    req, reporter.district, row_num, sheet, upload_ref,e)
                                continue#print ikosa 

                            try:
                                #chw = Reporter.objects.filter(national_id = reporter.national_id, telephone_moh = reporter.telephone_moh)
                                
                                #if chw.exists():                                
                                #    chw = update_reporter(row_num, sheet, reporter = chw[0])
                                #curl -s -D/dev/stdout 'http://127.0.0.1:8082/%2B250788301293/WHO?charset=UTF-8'
    
                                #else:
                                try:
                                    #chw = reporter
                                    try:
                                        chw.save()
                                        confirm = RegistrationConfirmation(reporter = chw)
                                        confirm.save()
                                    except IntegrityError, e:
                                        chw = Reporter.objects.get(national_id = chw.national_id, telephone_moh = chw.telephone_moh)
                                        confirm = RegistrationConfirmation.objects.get(reporter = chw)
                                        
                                    try:
                                        old_reporter = get_reporter(chw.national_id)
                                        old_reporter.location = old_registry.Location.objects.get(code = fosa_to_code(chw.health_centre.code))
                                        
                                        if chw.role.code.lower() == "asm":  old_reporter.groups.add(old_registry.ReporterGroup.objects.get(title='CHW'))
                                        elif chw.role.code.lower() == "binome":
                                            old_reporter.groups.add(old_registry.ReporterGroup.objects.get(title='Binome'))
                                            old_reporter.groups.remove(old_registry.ReporterGroup.objects.get(title='CHW'))
                                        if chw.village: old_reporter.village = chw.village.name
                                        else:   old_reporter.village = "Village Ntizwi" 
                                        old_reporter.language = chw.language.lower()
                                        old_reporter.save()
                                        chw.old_ref = old_reporter
                                        chw.save() 
                                        old_connection = get_connection(chw.telephone_moh, reporter = old_reporter)
                                        r = r+1
                                        #print r , old_reporter, old_connection
                                    except Exception, e:
                                        pass
                                    for c in reporter.__dict__:
                                            if c[0] == "_":  pass
                                            else:
                                                if reporter.__dict__[c] == '' or  reporter.__dict__[c] == None:
                                                    ikosa = set_warn("Row: %d ===>>> Warning: %s MISSING OR WRONG" % (int(row_num+1), c), \
                                                                    req, reporter.district, row_num, sheet, upload_ref)

                                except Exception, e:

                                    try:
                                        chw = Reporter.objects.filter(national_id = reporter.national_id, telephone_moh = reporter.telephone_moh)
                                        if chw.exists():
                                            chw = update_reporter(row_num, sheet, reporter = chw[0])
                                            ikosa = set_error("Row: %d ===>>> Error: %s" % ((row_num+1),"Duplicate Entry"), \
                                                                    req, reporter.district, row_num, sheet, upload_ref,e )
                                        else:
                                            ikosa = set_error("Row: %d ===>>> Error: %s" % ((row_num+1),e), \
                                                                    req, reporter.district, row_num, sheet, upload_ref,e )
                                    except Exception, e:
                                        ikosa = set_error("Row: %d ===>>> Error: Unknown (%s)" % ((row_num+1),e), \
                                                                    req, reporter.district, row_num, sheet, upload_ref,e )
                                        pass
     
                                    pass                                         
                                #r = r + 1
                                #print r, chw.surname, chw.given_name, chw.role, chw.sex, chw.education_level, chw.date_of_birth, chw.join_date, chw.national_id, chw.telephone_moh, chw.village, chw.cell, chw.sector, chw.health_centre, chw.referral_hospital, chw.district, chw.province, chw.nation, chw.created, chw.updated, chw.language         
                            except Exception, e:
                                #print e, row_num
                                pass
                            error_list, warnings = Error.objects.filter( upload_ref = upload_ref), Warn.objects.filter( upload_ref = upload_ref)
                        except Exception,e:
                                errornum+=1
                                continue

        else:
                form = UploadImportFileForm()
        if errornum >= 1: err="Error: %s"%e
        
        return render_to_response('chws/import.html', {'form': form,'error':error_list, 'warn':warnings, 'ref':upload_ref}, context_instance=RequestContext(req))

    except Exception,e:
        return render_to_response("ubuzima/404.html",{'error':e}, context_instance=RequestContext(req))
    

def process_import_file(import_file, session):
    """
    Open the uploaded file and save it to the temp file location specified
    in BATCH_IMPORT_TEMPFILE_LOCATION, adding the current session key to
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


def alert_to_start(reporter):
    Command().send_message(reporter.connections.get(backend__title="kannel"),"Muraho murakomeye! Umwaka mushya muhire. Twagirango tubamenyesheko mushobora gutangira kohereza ubutumwa ku buzima bw'umubyeyi n'umwana kuri numero 1110. Rapidsms numero 1110. Murakoze")


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


def get_reporter(national_id):
    try:
        reporter = old_registry.Reporter.objects.filter(alias = national_id)[0]
        return reporter
    except Exception, e:
        try:
            reporter = old_registry.Reporter(alias = national_id)
            reporter.save()
            return reporter
            
        except Exception, e:
            return None

def get_connection(telephone_moh, reporter = None):
    try:
        connection = old_registry.PersistantConnection.objects.filter(identity = telephone_moh)[0]
        if connection.reporter: return connection
        else:  
            connection.reporter = reporter
            connection.save()
            return connection
    except Exception, e:
        try:
            if reporter:

                backend = old_registry.PersistantBackend.objects.get(title="kannel")
                connection = old_registry.PersistantConnection(backend = backend, identity = telephone_moh, \
                                                                                        reporter = reporter, last_seen = timezone.localtime(timezone.now()))
                connection.save()
                return connection
            else:
                return None
        except Exception, e:
            return None

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
        return Nation.objects.get(name__icontains = name)
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
        sector = Sector.objects.filter(name__icontains = name, district = district)
        return sector[0]            
    except:
        sector = Sector.objects.filter(name__icontains = parse_l_r_name(name), district = district)
        if sector.exists(): return sector[0]
        else:   return None


def get_cell(name, sector):
    try:
        cell = Cell.objects.filter(name__icontains = name, sector = sector)
        return cell[0]            
    except:
        cell = Cell.objects.filter(name__icontains = parse_l_r_name(name), sector = sector)
        if cell.exists(): return cell[0]
        else:   return None

def get_village(name, cell):
    try:
        village = Village.objects.filter(name__icontains = name, cell = cell)
        return village[0]            
    except:
        village = Village.objects.filter(name__icontains = parse_l_r_name(name), cell = cell)
        if village.exists(): return village[0]
        else:   return None

def get_health_centre(name, district):
    try:
        hc = HealthCentre.objects.filter(name__icontains = name, district = district)
        return hc[0]           
    except:
        hc = HealthCentre.objects.filter(name__icontains = parse_l_r_name(name), district = district)
        if hc.exists(): return hc[0]
        else:   return None

def get_referral_hospital(name, district):
    try:
        hosp = Hospital.objects.filter(name__icontains = name, district = district)
        return hosp[0]            
    except:
        hosp = Hospital.objects.filter(name__icontains = parse_l_r_name(name), district = district)
        if hosp.exists(): return hc[0]
        else:   return None

        
def initialize_reporter(row, sheet):
    reporter = Reporter()
    reporter.national_id     = parse_alias(sheet.cell(row,7).value)
    reporter.telephone_moh   = parse_phone_number(sheet.cell(row,8).value)
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
    reporter.language       = reporter.language

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

def excel_regs_confirms(regs):
    workbook = create_workbook()
    sheet = create_worksheet(workbook, "Reporters")
    
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
