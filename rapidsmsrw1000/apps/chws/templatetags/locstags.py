from django.template import Library


register = Library()

@register.filter(name = 'to_type')
def to_type(object):
    return type(object)

