#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from rapidsmsrw1000.apps.reporters.models import *
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
            reps = Reporter.objects.all().order_by('id')
            for rep in reps:

                contact, created = Contact.objects.get_or_create(name = rep.alias)
                if rep.language:    contact.language = rep.language.lower()
                else:   contact.language = 'rw'   
                

                connections = Connection.objects.filter(contact = contact)

                backend, created = PersistantBackend.objects.get_or_create(title = "kannel", slug = 'kannel')
                
                backends = Backend.objects.all()
                for b in backends:
                    try:
                        persistant_connection = rep.connection()
                        identity = persistant_connection.identity if b.name != 'message_tester' else persistant_connection.identity.replace('+','')
                        connection, created = Connection.objects.get_or_create(contact = contact, backend = b, identity = identity)

                        kannel_connection, created = PersistantConnection.objects.get_or_create(backend = backend, identity = persistant_connection.identity)
                        kannel_connection.reporter = rep
                        print rep.id, b, contact, connection, kannel_connection

                        connection.save()
                        kannel_connection.save()
                    except:
                        continue
                
                contact.save()
                
            
        except Exception, e:
            print e

        print "Complete."

        if self.dry:
            print "DRY RUN Complete."
