from acmeproxy.proxy.models import Authorisation, Response


def create_authorisation(name):
    Authorisation.objects.create(
        name=name, secret="test_secret", created_by_ip="127.0.0.1"
    )


def create_response(name):
    Response.objects.create(
        name=name, response="test_response", created_by_ip="127.0.0.1"
    )
