import sys
import os
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import dateparse, timezone
from django.db.models import Q

from acmeproxy.proxy.models import *

class Command(BaseCommand):
    help = 'Called by PowerDNS to exchange DNS data'

    @staticmethod
    def format_data(qname, qtype, answer, ttl=60):
        return '\t'.join([qname, 'IN', qtype, str(ttl), '1', answer])

    @staticmethod
    def send(answer_tag, answer_data=None):
        if answer_data:
            answer_data = "\t{}".format(answer_data)
        else:
            answer_data = ''
        line =  "{}{}\n".format(answer_tag, answer_data)
        sys.stdout.write(line)
        sys.stdout.flush()

    @staticmethod
    def strip_labels(name, count):
        return ".".join(name.split(".")[count:])

    def generate_records(self):
        responses = Response.objects.filter(
            Q(expired_at__gt=timezone.now()) |
            Q(expired_at__isnull=True)
        )
        records = [] 

        for response in responses:
            # Serve the challenge TXT record for the requested zone
            records.append(
                {
                    'name': "_acme-challenge.%s" % response.name,
                    'type': 'TXT',
                    'ttl': 5,
                    'content': response.response,
                }
            )

            # In case just the _acme-challenge.foo name was delegated, ensure authority at that level
            records.append( 
                {
                    'name': "_acme-challenge.%s" % response.name,
                    'type': 'SOA',
                    'ttl': 5,
                    'content': '%s. %s. %s 0 0 0 0' % (
                        settings.ACMEPROXY_SOA_HOSTNAME,
                        settings.ACMEPROXY_SOA_CONTACT,
                        str(int(time.time())),
                    ),
                }
            )
            records.append( # Serve NS for _acme-challenge.foo.example.com
                {
                    'name': "_acme-challenge.%s" % response.name,
                    'type': 'NS',
                    'ttl': 5,
                    'content': settings.ACMEPROXY_SOA_HOSTNAME,
                }
            )
            records.append( # Serve CAA for _acme-challenge.foo.example.com
                {
                    'name': "_acme-challenge.%s" % response.name,
                    'type': 'CAA',
                    'ttl': 5,
                    'content': '0 issue "letsencrypt.org"',
                }
            )

            # Also claim to be authoritative for foo.example.com and example.com to handle CAA for the various ways in which the challenge
            # might have been delegated (e.g. at the foo.example.com or example.com levels)
       
            for depth in (0, 1):
                extra_zone_name = self.strip_labels(response.name, depth)

                records.append(
                    {
                        'name': extra_zone_name,
                        'type': 'SOA',
                        'ttl': 5,
                        'content': '%s. %s. %s 0 0 0 0' % (
                            settings.ACMEPROXY_SOA_HOSTNAME,
                            settings.ACMEPROXY_SOA_CONTACT,
                            str(int(time.time())),
                        ),
                    }
                )
                records.append(
                    {
                        'name': extra_zone_name,
                        'type': 'NS',
                        'ttl': 5,
                        'content': settings.ACMEPROXY_SOA_HOSTNAME,
                    }
                )
                records.append(
                    {
                        'name': extra_zone_name,
                        'type': 'CAA',
                        'ttl': 5,
                        'content': '0 issue "letsencrypt.org"',
                    }
                )

        return records

    def handle(self, *args, **options):
        # handshake and accept version 1 of the ABI
        line = sys.stdin.readline()
        query, version = line.strip().split()
        if query != 'HELO' and version != '1':
            self.send('FAIL')
            sys.exit(1)
        
        self.send('OK', 'ACME Proxy API')

        # loop forever answering questions
        while True:
            line = sys.stdin.readline()

            try:
                question_type, qname, qclass, qtype, id, remote_ip = line.strip().split()
            except ValueError:
                if line.startswith('DEBUGQUIT'):
                    sys.exit(0)
                else:
                    continue
       

            records = self.generate_records()
            found = 0
            if question_type == 'Q':
                for record in records:
                    if qtype in ('ANY', record['type']) and qname.lower() == record['name']:
                        found = found + 1
                        self.send('DATA', self.format_data(qname, record['type'], record['content'], record['ttl']))

            self.send('END')
