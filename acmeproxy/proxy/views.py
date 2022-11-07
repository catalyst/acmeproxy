import hmac

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from rest_framework import serializers
from rest_framework.response import Response as APIResponse
from rest_framework.views import APIView

from .models import Account, Authorisation, Response
from .utils import client_ip


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


class PublishResponseSerializer(serializers.Serializer):
    name = serializers.CharField()
    response = serializers.CharField()
    secret = serializers.CharField()


class PublishResponse(APIView):
    def post(self, request, format=None):
        serializer = PublishResponseSerializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse(serializer.errors, status=400)

        name = serializer.data["name"].lower()
        response = serializer.data["response"]
        secret = serializer.data["secret"]

        authorisation = get_authorisation(name, secret)

        if authorisation:
            try:
                db_response = Response(
                    name=name, response=response, created_by_ip=client_ip(request)
                )
                db_response.save()
            except:
                return APIResponse(
                    {"result": False, "error": "Could not save response in database"},
                    status=500,
                )
            else:
                return APIResponse(
                    {"result": {"authorisation": authorisation.name, "published": True}}
                )

        return APIResponse(
            {"result": False, "error": "Invalid authorisation token"}, status=403
        )


class NameSecretSerializer(serializers.Serializer):
    name = serializers.CharField()
    secret = serializers.CharField()


class ExpireResponse(APIView):
    def post(self, request, format=None):
        serializer = NameSecretSerializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse(serializer.errors, status=400)

        name = serializer.data["name"].lower()
        secret = serializer.data["secret"]

        authorisation = get_authorisation(name, secret)

        if authorisation:
            expired = (
                Response.objects.filter(name__iexact=name).update(
                    expired_at=timezone.now()
                )
                > 0
            )
            return APIResponse(
                {"result": {"authorisation": authorisation.name, "expired": expired}}
            )

        return APIResponse(
            {"result": False, "error": "Invalid authorisation token"}, status=403
        )


class NameSecretOptionalSerializer(serializers.Serializer):
    name = serializers.CharField()
    secret = serializers.CharField()


# XXX: multiple authorisations for a single domain are permitted
class CreateAuthorisation(APIView):
    def post(self, request, format=None):
        serializer = NameSecretOptionalSerializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse(serializer.errors, status=400)

        name = serializer.data["name"].lower()
        secret = serializer.data.get("secret")

        account_query = Account.objects.filter(secret=secret)
        if len(account_query) != 1:
            return APIResponse(
                {"result": False, "error": "Invalid account token"}, status=403
            )
        else:
            account = account_query[0]
            allowed = False
            for permit_name in account.permit_domains.replace(" ", "").split(","):
                if (permit_name == "." or
                        (permit_name.startswith(".") and name.endswith(permit_name)) or
                        (not permit_name.startswith(".") and permit_name == name)):
                    allowed = True
                    break
            if not allowed:
                return APIResponse(
                    {
                        "result": False,
                        "error": "Changes to this domain are not permitted with this account token",
                    },
                    status=403,
                )

        db_authorisation = Authorisation(
            name=name, created_by_ip=client_ip(request), account=account
        )
        db_authorisation.reset_secret()

        try:
            db_authorisation.save()
        except:
            return APIResponse(
                {"result": False, "error": "Could not save authorisation in database"},
                status=500,
            )

        return APIResponse(
            {
                "result": {
                    "authorisation": db_authorisation.name,
                    "secret": db_authorisation.secret,
                }
            }
        )


class ExpireAuthorisation(APIView):
    def post(self, request, format=None):
        serializer = NameSecretSerializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse(serializer.errors, status=400)

        name = serializer.data["name"].lower()
        secret = serializer.data["secret"]

        authorisation = get_authorisation(name, secret)

        if authorisation:
            try:
                authorisation.reset_secret()
                authorisation.save()
            except:
                return APIResponse(
                    {
                        "result": False,
                        "error": "Could not save authorisation in database",
                    },
                    status=500,
                )
            else:
                return APIResponse(
                    {
                        "result": {
                            "authorisation": authorisation.name,
                            "secret": authorisation.secret,
                        }
                    }
                )

        return APIResponse(
            {"result": False, "error": "Invalid authorisation token"}, status=403
        )
