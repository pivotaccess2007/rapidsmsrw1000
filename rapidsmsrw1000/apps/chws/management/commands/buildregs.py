#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from rapidsmsrw1000.apps.chws.dbmodule import *
from rapidsms.models import Contact, Connection, Backend
from django.core.management.base import BaseCommand
from optparse import make_option

class Command(BaseCommand):
    help = "Build our Contacts for each CHW registered in old registry."
    option_list = BaseCommand.option_list + (
        make_option('-d', '--dry',
                    action='store_true',
                    dest='dry',
                    default=False,
                    help='Executes a dry run, doesnt send messages or update the db.'),
        )
	
    def handle(self, **options):
        print "Running contacts rebuild.."

        self.dry = options['dry']

        if self.dry:
            self.dry = True
            print "DRY RUN -- No messages will be sent, no database commits made."

        try:
            update_empty_contact_connections()                
            
        except Exception, e:
            print e

        print "Complete."

        if self.dry:
            print "DRY RUN Complete."
