from django import template
from django.utils.datastructures import SortedDict

register = template.Library()

@register.filter(name='twof')
def listsort(value):
	try:	return "%.2f" % round(value,2)
	except:	return value
     
