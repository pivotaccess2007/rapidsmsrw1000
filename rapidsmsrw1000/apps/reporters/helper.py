from reporters.models import *

class Helper(Reporter):
	
	
	def search_chw(cls, nid=None,conn=None):
		""" Given a national id of a reporter or knowing his/her connection ( any used used connection which is the number of the phone and the backends the number was enabled to report via) find respectively reporter infos, backends registered on, and connections opened. """
		result = {}
		try:
			if nid:
				result['connections'] = PersistantConnection.objects.filter(reporter = Reporter.objects.get (alias = nid))			
				result['backend'] = PersistantBackend.objects.filter(backend__in = result['connections'])
				result['reporter'] = Reporter.objects.get( alias = nid )
			if conn:
				result['reporter'] = Reporter.objects.get( pk = conn.reporter.pk )
				result['connections'] = PersistantConnection.objects.filter(reporter = result['reporter'])
				result['backend'] = PersistantBackend.objects.filter(backend__in = result['connections'])
		except Exception: pass
	
		return result
 
		
