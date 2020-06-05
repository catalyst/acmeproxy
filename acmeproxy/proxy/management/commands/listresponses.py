from collections import OrderedDict

from tabulate import tabulate

from django.core.management.base import BaseCommand, CommandError
from django.utils import dateparse, timezone

from acmeproxy.proxy.models import *

class Command(BaseCommand):
    help = 'List all published responses for a given date range'

    def add_arguments(self, parser):
            parser.add_argument('--start', default=None, help="if specified, return only records created after this time")
            parser.add_argument('--end', default=None, help="if specified, return only records created before this time")
            parser.add_argument('--name', default=None, help="if specified, return only records for this name")
            
    def handle(self, *args, **options):
        query = {}

        if options['start'] is not None:
            query['created_at__gt'] = dateparse.parse_date(options['start'])
            if query['created_at__gt'] is None:
                raise CommandError('Invalid start date')

        if options['end'] is not None:
            query['created_at__lt'] = dateparse.parse_date(options['end'])
            if query['created_at__lt'] is None:
                raise CommandError('Invalid end date')

        if options['name'] is not None:
            query['name__iexact'] = options['name']

        responses = Response.objects.filter(**query)
        if len(responses) < 1: 
            raise CommandError('No responses found')

        # this is pretty inefficient but the table is likely to be small
        table = [{k:v for (k,v) in response.__dict__.items() if k in ('expired_at', 'created_at', 'created_by_ip', 'name')} for response in responses]
        table = [OrderedDict(sorted(entry.items(), key=lambda x:x[0], reverse=True)) for entry in table]
        print(tabulate(table, headers="keys"))

