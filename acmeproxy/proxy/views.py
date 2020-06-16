import hmac

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import Authorisation, Response


# stolen from https://stackoverflow.com/a/4581997
def client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def get_authorisation(name, secret):
    """
    Attempts to find a valid authorisation for the given name and secret combination.
    """

    try:  # try and find an explicit authorisation
        authorisation = Authorisation.objects.get(name__iexact=name)
        if not hmac.compare_digest(authorisation.secret, secret):
            raise ObjectDoesNotExist
    except ObjectDoesNotExist:
        return False

    return authorisation


@csrf_exempt
def publish_response(request):
    """
    Publish an ACME challenge response in to the DNS.
    """

    if request.method != "POST":
        return JsonResponse({"result": False}, status=405)

    try:
        name = request.POST["name"].lower()
        response = request.POST["response"]
        secret = request.POST["secret"]
    except:
        return JsonResponse({"result": False}, status=400)

    authorisation = get_authorisation(name, secret)

    if authorisation:
        try:
            db_response = Response(
                name=name, response=response, created_by_ip=client_ip(request)
            )
            db_response.save()
        except:
            return JsonResponse(
                {"result": False, "error": "Could not save response in database"},
                status=500,
            )
        else:
            return JsonResponse(
                {"result": {"authorisation": authorisation.name, "published": True}}
            )

    return JsonResponse(
        {"result": False, "error": "Invalid authorisation token"}, status=403
    )


@csrf_exempt
def expire_response(request):
    """
    Once a challenge has been used the client may optionally mark it as such, preventing further requests.
    """

    if request.method != "POST":
        return JsonResponse(
            {"result": False, "error": "Improper method, only POST is allowed"},
            status=405,
        )

    try:
        name = request.POST["name"].lower()
        secret = request.POST["secret"]
    except:
        return JsonResponse(
            {"result": False, "error": "Missing parameters in POST"}, status=400
        )

    authorisation = get_authorisation(name, secret)

    if authorisation:
        expired = (
            Response.objects.filter(name__iexact=name).update(expired_at=timezone.now())
            > 0
        )
        return JsonResponse(
            {"result": {"authorisation": authorisation.name, "expired": expired}}
        )

    return JsonResponse(
        {"result": False, "error": "Invalid authorisation token"}, status=403
    )


@csrf_exempt
def create_authorisation(request):
    """
    Create a new authorisation and return the secret key.
    """

    if request.method != "POST":
        return JsonResponse(
            {"result": False, "error": "Improper method, only POST is allowed"},
            status=405,
        )

    try:
        name = request.POST["name"].lower()
        secret = request.POST.get("secret", "")
    except:
        return JsonResponse(
            {"result": False, "error": "Missing parameters in POST"}, status=400
        )

    if settings.ACMEPROXY_AUTHORISATION_CREATION_SECRETS is not None:
        user = settings.ACMEPROXY_AUTHORISATION_CREATION_SECRETS.get(secret, None)
        if user is None:
            return JsonResponse(
                {"result": False, "error": "Invalid account token"}, status=403
            )
        else:
            allowed = True
            if "permit" in user:
                allowed = False
                for permit_name in user["permit"]:
                    if (permit_name.startswith(".") and name.endswith(permit_name)) or (
                        not permit_name.startswith(".") and permit_name == name
                    ):
                        allowed = True
                        break
            if not allowed:
                return JsonResponse(
                    {
                        "result": False,
                        "error": "Changes to this domain are not permitted with this account token",
                    },
                    status=403,
                )

            account = user["name"]
    else:
        account = ""

    db_authorisation = Authorisation(
        name=name, created_by_ip=client_ip(request), account=account
    )
    db_authorisation.reset_secret()

    try:
        db_authorisation.save()
    except:
        return JsonResponse(
            {"result": False, "error": "Could not save authorisation in database"},
            status=500,
        )

    return JsonResponse(
        {
            "result": {
                "authorisation": db_authorisation.name,
                "secret": db_authorisation.secret,
            }
        }
    )


@csrf_exempt
def expire_authorisation(request):
    """
    Expire an existing authorisation secret key.
    """

    if request.method != "POST":
        return JsonResponse(
            {"result": False, "error": "Improper method, only POST is allowed"},
            status=405,
        )

    try:
        name = request.POST["name"].lower()
        secret = request.POST["secret"]
    except:
        return JsonResponse(
            {"result": False, "error": "Missing parameters in POST"}, status=400
        )

    authorisation = get_authorisation(name, secret)

    if authorisation:
        try:
            authorisation.reset_secret()
            authorisation.save()
        except:
            return JsonResponse(
                {"result": False, "error": "Could not save authorisation in database"},
                status=500,
            )
        else:
            return JsonResponse(
                {
                    "result": {
                        "authorisation": authorisation.name,
                        "secret": authorisation.secret,
                    }
                }
            )

    return JsonResponse(
        {"result": False, "error": "Invalid authorisation token"}, status=403
    )
