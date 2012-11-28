from apps.ubuzima.app import *
class Test():
	
	def test_me(self, text):
		reporter, created = Reporter.objects.get_or_create(alias = "1198680069759062", village = "Muhoza", location = Location.objects.get(code = 'F316'))
		connection = PersistantConnection(backend = PersistantBackend.objects.get(title = "pygsm"), identity = '078860270', reporter = reporter)
		
		message = rapidsms.message.Message( connection = connection, person = reporter, text = text)
		message.reporter = reporter
		app = App(rapidsms.app.App)
		results = app.keyword.match(app, message.text)
		func , captures = results
		return func(app, message, *captures)


###TEST CASE
#msg = "BIR 1198156435491265 TW 01 13.02.2011 GI PM NP HP BF1 WT72.3"
#from apps.thousanddays.reports.test import *
#x = Test()
#x.test_me(msg)
