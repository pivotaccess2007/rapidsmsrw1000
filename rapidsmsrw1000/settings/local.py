from .base import *

#CELERY_ALWAYS_EAGER = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'rapidsmsrw1000',
        'USER': 'rapidsmsrw1000',
        'PASSWORD': '123456',
        'HOST': '',
        'PORT': '',
    }
}


#import warnings
#warnings.filterwarnings(
#        'error', r"DateTimeField received a naive datetime",
#        RuntimeWarning, r'django\.db\.models\.fields')
