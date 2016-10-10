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

def lookup(request, qname, qtype):
    """
    Queried by PowerDNS to return the public challenge response and other sundry DNS stuff for a name. XXX This method could be tidier.
    """

    qname_parts = qname.split('.')
    threshold = timezone.now() - timedelta(minutes=5)

    if qname_parts[0].lower() == '_acme-challenge': # determine the underlying zone name for a request
        zone_name = '.'.join(qname_parts[1:]).lower().strip('.')
        request_challenge = True
    else:
        zone_name = qname.lower().strip('.')
        request_challenge = False

    try: # find the newest response for a given zone name
        response = Response.objects.filter(name__iexact=zone_name, created_at__gt=threshold).order_by('-created_at')[0]
        if not response.live():
            raise IndexError
    except IndexError:
        return(JsonResponse({'result': []}))

    result = []
    if not request_challenge and qtype in ('ANY', 'SOA'):
        result.append(
            {
                "qtype": "SOA",
                "qname": "%s" % zone_name,
                "content": "%s. %s. %s 0 0 0 0" % (settings.ACMEPROXY_SOA_HOSTNAME, settings.ACMEPROXY_SOA_CONTACT, str(int(time.time()))),
                "ttl": 5,
            }
        )
    if request_challenge and qtype in ('ANY', 'TXT'):
        result.append(
            {
                "qtype": "TXT",
                "qname": "%s" % qname,
                "content": response.response,
                "ttl": 5,
            }
        )

    response = {
        "result": result,
    }

    return JsonResponse(response)

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
        suffix_match = False # XXX suffix matching is disabled until a security verification is implemented (e.g. a 2nd DNS challenge)(request.POST.get('suffix_match', 'false').lower() == 'true')
    except:
        return JsonResponse({'result': False}, status=400)

    db_authorisation = Authorisation(name=name, suffix_match=suffix_match, created_by_ip=client_ip(request))
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

