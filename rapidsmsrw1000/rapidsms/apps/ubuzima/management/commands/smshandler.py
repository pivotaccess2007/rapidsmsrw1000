#!/usr/bin/env python
# I receive and I send message to an appropriate destination, as sms
# First to use me you need to configure the modem on ttyUSB port on Linux or COM port on Windows OS
## put this file in app_name/management/commands/

import time
from pygsm import GsmModem
import urllib2
from django.core.management.base import BaseCommand
# Because you don't use any sms framework, please configure you modem here, as well as your application
## Feel fre to modify your host, the ports for both the application and the modem

conf = {'host': '127.0.0.1', 'port': '8000', 'url': '/sms_interface/', 'gsm': {'port':'/dev/ttyUSB1'}}


class Command(BaseCommand):
	help = "This command need to be started whenever the application is running, of course after executing runserver."
	print conf['gsm']
	gsm = GsmModem( port = conf['gsm']['port'], logger=GsmModem.debug_logger).boot()

	def handle(self, **options):
		print "Transmitting SMS..."
		cmd = SmsHandler(self.gsm).transmit_sms()

class SmsHandler(object):
	def __init__(self, modem):
		self.modem = modem

	def receive(self, msg):
		req = self.create_request(msg)
		print "METHOD: %s    DATA: %s"% (req.get_method(), req.data)
		if req:
			response =  self.get_response(req)
			print response ## to see how it looks before you can send a correct message.
		msg.respond(response.msg)

	def transmit_sms(self):
		while True:
			msg = self.modem.next_message()

			if msg is not None:
				self.receive(msg)

			time.sleep(2)

	def create_request(data):
		try:
			url="http://%s:%s%s"%(conf["host"],conf["port"],conf['url'])
			request = urllib2.Request(url, data)
			
			return request
		except:
			pass
		return False

	def get_response(request):
		try:
			response = urllib2.urlopen(request)
		except urllib2.HTTPError, e:
			response=e
		except urllib2.URLError, e:
			response=e		
		return response






