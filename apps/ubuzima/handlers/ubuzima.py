#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact

import re
from apps.ambulances.models import *
from apps.locations.models import Location
from apps.ubuzima.models import *
from apps.reporters.models import *
from django.utils.translation import ugettext as _
from django.utils.translation import activate, get_language
from decimal import *
from exceptions import Exception
import traceback
from datetime import *
from time import *
from django.db.models import Q


class UbuzimaHandler(KeywordHandler):
    
    # map of language code to language name
    LANG = { 'en': 'English',
             'fr': 'French',
             'rw': 'Kinyarwanda' }

    sep="[;,'\"+&*#@\s]"
    ####
