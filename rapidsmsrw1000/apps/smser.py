#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf import settings
import urllib2
import time

class Smser(object):
    help = "To send SMS"	
	
    def send_message_via_kannel(self, identity, message):
	
        try:
            conf = settings.INSTALLED_BACKENDS

            url = "%s?to=%s&text=%s&password=%s&user=%s" % (
                conf['kannel-smpp']['sendsms_url'],
                urllib2.quote(identity.strip()), 
                urllib2.quote(message),
                conf['kannel-smpp']['sendsms_params']['password'],
                conf['kannel-smpp']['sendsms_params']['username'])

            f = urllib2.urlopen(url, timeout=10)
            if f.getcode() / 100 != 2:
                print "Error delivering message to URL: %s" % url
                raise RuntimeError("Got bad response from router: %d" % f.getcode())

            # do things at a reasonable pace
            time.sleep(.2)
            return True
        except Exception, e:
            return False




	

