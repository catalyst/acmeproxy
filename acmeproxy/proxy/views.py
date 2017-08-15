from datetime import timedelta
import time

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import *

# stolen from https://stackoverflow.com/a/4581997
def client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_authorisation(name, secret):
    """
    Attempts to find a valid authorisation for the given name and secret combination.
    """

    try: # try and find an explicit authorisation, or a wildcard for one label up
        authorisation = Authorisation.objects.get(name__iexact=name, secret=secret)
    except ObjectDoesNotExist:
        try:
            authorisation = Authorisation.objects.get(name__iexact='.'.join(name.split('.')[1:]), secret=secret, suffix_match=True)
        except ObjectDoesNotExist:
            return(False)

    return(authorisation)

def create_records(name_records, response=None, name=None):
    """
    Create the appropriate DNS records for the given response/name
    in the name records database. This operates using one of two
    parameters:
    * name - used for upper level domain names from the zones for which
             challenge responses are made, does NOT create _acme-challenge
             SOA and TXT records
    * response - used for challenge response domain name queries, creates
                 _acme-challenge subdomain SOA and TXT records using the
                 information from the Response object
    """

    if not response and name: # Upper level domain query.
        name_records[name] = {}
    elif response and not name: # Challenge response domain query.
        name = response.name
        name_records[name] = {}
        acme_name = '_acme-challenge.%s' % name
        name_records[acme_name] = {}
    elif response and name:
        raise RuntimeError(
            'response and name are mutually exclusive: response=%s, name=%s' %
                    (response, name),
        )
    else:
        raise RuntimeError(
            'one of response and name should be specified: response=%s, name=%s' %
                    (response, name),
        )

    # Certificate Authority Authorisation (CAA) record, authorising
    # Let's Encrypt to generate certificates for the zone.
    record = Record.objects.create()
    record.name = name
    record.type = 'CAA'
    record.ttl = 5
    record.content = '0 issue "letsencrypt.org"'
    name_records[name]['CAA'] = record

    # Start Of Authority (SOA) record, specifying authoritative information about
    # the DNS zone.
    record = Record.objects.create()
    record.name = name
    record.type = 'SOA'
    record.ttl = 5
    record.content = '%s. %s. %s 0 0 0 0' % (
        settings.ACMEPROXY_SOA_HOSTNAME,
        settings.ACMEPROXY_SOA_CONTACT,
        str(int(time.time())),
    )
    name_records[name]['SOA'] = record

    # These records only get created if create_records gets passed
    # a full record with a challenge response stored in it, rather
    # than just a name.
    if response:
        # Create ACME challenge response subdomain equivalent.
        record = Record.objects.create()
        record.name = acme_name
        record.type = 'SOA'
        record.ttl = 5
        record.content = '%s. %s. %s 0 0 0 0' % (
            settings.ACMEPROXY_SOA_HOSTNAME,
            settings.ACMEPROXY_SOA_CONTACT,
            str(int(time.time())),
        )
        name_records[acme_name]['SOA'] = record

        # TXT records to store the response for the ACME challenge.
        record = Record.objects.create()
        record.name = name
        record.type = 'TXT'
        record.ttl = 5
        record.content = response.response
        name_records[name]['TXT'] = record

        record = Record.objects.create()
        record.name = acme_name
        record.type = 'TXT'
        record.ttl = 5
        record.content = response.response
        name_records[acme_name]['TXT'] = record

def lookup(request, qname, qtype):
    """
    Queried by PowerDNS to return the public challenge response and other sundry DNS stuff for a name. XXX This method could be tidier.
    """

    # Create the record database and the TTL value for its
    # records.
    name_records = {}
    threshold = timezone.now() - timedelta(minutes=5)

    # Get the query name from the input, and filter the zone name
    # from it, if it's an ACME challenge request.
    query_name = qname.strip('.')

    query_name_parts = query_name.split('.')
    if query_name_parts[0].lower() == '_acme-challenge':
        zone_name = '.'.join(query_name_parts[1:]).lower()
    else:
        zone_name = query_name.lower()

    # Fill the database with the minimum amount of records
    # to handle the query.
    response_filter = Response.objects.filter(name__iexact=zone_name)
    if response_filter:
        create_records(name_records, response=response_filter[0])
    else:
        response_filter = Response.objects.filter(name__iregex=r'^[^\.]*\.?%s$' % zone_name)
        if response_filter:
            create_records(name_records, name=zone_name)
        else: # No records at all related to this zone name: empty response.
            return JsonResponse({'result': []})

    # Get requested records and form a JSON response with them.
    records = ()
    results = []

    if qtype == 'ANY':
        records = name_records[query_name].values()
    elif qtype in name_records[query_name]:
        records = (name_records[query_name][qtype],)

    if records:
        for record in records:
            results.append(
                {
                    'qtype': record.type,
                    'qname': record.name,
                    'ttl': record.ttl,
                    'content': record.content,
                }
            )

    return JsonResponse({'result': results})

def not_implemented(request):
    """
    Returned to PowerDNS for all unimplemented API endpoints.
    """

    response = {
        "result": False,
    }
    return JsonResponse(response, status=501)

@csrf_exempt
def publish_response(request):
    """
    Publish an ACME challenge response in to the DNS.
    """

    if request.method != 'POST':
        return JsonResponse({'result': False}, status=405)

    try:
        name = request.POST['name'].lower()
        response = request.POST['response']
        secret = request.POST['secret']
    except:
        return JsonResponse({'result': False}, status=400)

    authorisation = get_authorisation(name, secret)

    if authorisation:
        try:
            db_response = Response(name=name, response=response, created_by_ip=client_ip(request))
            db_response.save()
        except:
            return(JsonResponse({'result': False}, status=500))
        else:
            return(JsonResponse({"result": {'authorisation': authorisation.name, 'suffix_match': authorisation.suffix_match, 'published': True}}))

    return(JsonResponse({'result': False}, status=403))
    
@csrf_exempt
def expire_response(request):
    """
    Once a challenge has been used the client may optionally mark it as such, preventing further requests.
    """

    if request.method != 'POST':
        return JsonResponse({'result': False}, status=405)

    try:
        name = request.POST['name'].lower()
        secret = request.POST['secret']
    except:
        return JsonResponse({'result': False}, status=400)
    
    authorisation = get_authorisation(name, secret)
       
    if authorisation:
        expired = Response.objects.filter(name__iexact=name).update(expired_at=timezone.now()) > 0
        return JsonResponse({"result": {'authorisation': authorisation.name, 'suffix_match': authorisation.suffix_match, 'expired': expired}})
    
    return(JsonResponse({'result': False}, status=403))

@csrf_exempt
def create_authorisation(request):
    """
    Create a new authorisation and return the secret key.
    """

    if request.method != 'POST':
        return JsonResponse({'result': False}, status=405)

    try:
        name = request.POST['name'].lower()
        suffix_match = (request.POST.get('suffix_match', 'false').lower() == 'true')
        secret = request.POST.get('secret', '')
    except:
        return JsonResponse({'result': False}, status=400)

    if settings.ACMEPROXY_AUTHORISATION_CREATION_SECRETS is not None:
        if secret not in settings.ACMEPROXY_AUTHORISATION_CREATION_SECRETS:
            return JsonResponse({'result': False}, status=403)
        else:
            account = settings.ACMEPROXY_AUTHORISATION_CREATION_SECRETS[secret]
    else:
        account = ''

    db_authorisation = Authorisation(name=name, suffix_match=suffix_match, created_by_ip=client_ip(request), account=account)
    db_authorisation.reset_secret()

    try:
        db_authorisation.save()
    except:
        return JsonResponse({'result': False}, status=500)

    return JsonResponse({"result": {'authorisation': db_authorisation.name, 'suffix_match': db_authorisation.suffix_match, 'secret': db_authorisation.secret}})
    
@csrf_exempt
def expire_authorisation(request):
    """
    Expire an existing authorisation secret key.
    """

    if request.method != 'POST':
        return JsonResponse({'result': False}, status=405)

    try:
        name = request.POST['name'].lower()
        secret = request.POST['secret']
    except:
        return JsonResponse({'result': False}, status=400)

    authorisation = get_authorisation(name, secret)
       
    if authorisation:
        try:
            authorisation.reset_secret()
            authorisation.save()
        except:
            return JsonResponse({'result': False}, status=500)
        else:
            return JsonResponse({"result": {'authorisation': authorisation.name, 'suffix_match': authorisation.suffix_match, 'secret': authorisation.secret}})
    
    return(JsonResponse({'result': False}, status=403))

