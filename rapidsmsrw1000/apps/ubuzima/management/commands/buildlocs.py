#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from rapidsmsrw1000.apps.ubuzima.dbmodule import *
from django.core.management.base import BaseCommand
from optparse import make_option

class Command(BaseCommand):
    help = "Build our Table locations. Run in the cron, daily at 1 am"
    option_list = BaseCommand.option_list + (
        make_option('-d', '--dry',
                    action='store_true',
                    dest='dry',
                    default=False,
                    help='Executes a dry run, doesnt send messages or update the db.'),
        )
	
    def handle(self, **options):
        print "Running locations rebuild.."

        self.dry = options['dry']

        if self.dry:
            self.dry = True
            print "DRY RUN -- No messages will be sent, no database commits made."

        try:
            print "SQL"
            solve_old_sql()
            print "FACILITY"
            hc_loc_short_creation()
            print "FIELDS"
            build_old_fields()
            print "EDD"
            build_edd()
            print "REPORTER"
            locate_reporter()
            print "PATIENT"
            locate_patient()
            print "USER"
            locate_user()
            print "REPORT"
            locate_report()
            print "FIELD"
            locate_field()
            print "PROVINCE"
            import_provinces()
            print "DISTRICT"
            import_districts()
            print "SECTOR"
            import_sectors()
            print "CELL"
            import_cells()
            print "VILLAGE"
            #import_villages()
            print "CARD"
            import_cardcodes()
            print "REPORT TYPE"
            initialize_reporttypes()
            print "LOCATIONS"
            update_locations()
            print "REFUSAL"
            locate_refusal()
            print "DEPARTURE"
            locate_departure()
            print "REMINDER"
            locate_reminder()
            print "ALERT"
            locate_alert()
            
        except Exception, e:
            print e

        print "Complete."

        if self.dry:
            print "DRY RUN Complete."
