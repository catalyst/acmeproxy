from collections import OrderedDict

from django.core.management.base import BaseCommand, CommandError
from tabulate import tabulate

from acmeproxy.proxy.models import Authorisation


class Command(BaseCommand):
    help = "List all of the granted authorisations"

    def handle(self, *args, **options):
        authorisations = Authorisation.objects.all()
        if len(authorisations) < 1:
            raise CommandError("No authorisations found")

        # this is pretty inefficient but the table is likely to be small
        table = [
            {
                k: v
                for (k, v) in authorisation.__dict__.items()
                if k in ("account", "created_at", "created_by_ip", "name")
            }
            for authorisation in authorisations
        ]
        table = [
            OrderedDict(sorted(entry.items(), key=lambda x: x[0], reverse=True))
            for entry in table
        ]

        print(tabulate(table, headers="keys"))
