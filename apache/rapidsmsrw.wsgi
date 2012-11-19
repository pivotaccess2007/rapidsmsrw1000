import os
import sys

# set up python path and virtualenv
activate_this = '/home/zigama/projects/python/virtualenvs/RapidSMS-Rwanda/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

filedir = os.path.dirname(__file__)

rootpath = os.path.join(filedir, "..")
sys.path.append(os.path.join(rootpath))
sys.path.append(os.path.join(rootpath,'apps'))
#sys.path.append(os.path.join(rootpath,'rapidsms'))
#sys.path.append(os.path.join(rootpath,'webui'))
sys.path.append(os.path.join(rootpath,'lib','rapidsms'))
#sys.path.append(os.path.join(rootpath,'apps','ubuzima'))


#os.environ['RAPIDSMS_INI'] = os.path.join(rootpath,'rapidsms.ini')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
os.environ["RAPIDSMS_HOME"] = rootpath

import settings


#sys.path.append("/home/zigama/projects/python/virtualenvs/RapidSMS-Rwanda/RapidSMS-Rwanda")

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()


