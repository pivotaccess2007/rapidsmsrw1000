
from django.template import Library


register = Library()

@register.filter(name = 'to_class_name')
def to_class_name(object):
    return object.__class__.__name__

  
