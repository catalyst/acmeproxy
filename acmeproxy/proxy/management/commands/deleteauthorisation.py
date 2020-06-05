from django.core.management.base import BaseCommand, CommandError
from acmeproxy.proxy.models import *

class Command(BaseCommand):
    help = 'Delete an authorisation'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str)

    def handle(self, *args, **options):
        name = options['name']

        try:
            authorisation = Authorisation.objects.get(name__iexact=name)
        except Authorisation.DoesNotExist:
            raise CommandError('Authorisation "%s" does not exist' % name)

        try:
            authorisation.delete()
        except:
            raise CommandError('Could not delete authorisation "%s"' % name)
        else:
            self.stdout.write('Successfully deleted authorisation "%s"' % name)
