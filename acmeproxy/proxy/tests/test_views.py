import pytest

from acmeproxy.proxy.models import Authorisation, Response


@pytest.mark.django_db
class TestAuthroisation:
    def test_create_authorisation(self, client):
        resp = client.post("/create_authorisation", data={"name": "example.com"})
        assert resp.status_code == 200
        assert resp.json()["result"]["authorisation"] == "example.com"

    def test_create_authorisation_mixed_case(self, client):
        resp = client.post("/create_authorisation", data={"name": "exAMplE.cOm"})
        assert resp.status_code == 200
        assert resp.json()["result"]["authorisation"] == "example.com"

    def test_create_authorisation_missing_name(self, client):
        resp = client.post("/create_authorisation", data={})
        assert resp.status_code == 400
        assert resp.json()["result"] is False

    def test_create_authorisation_set_secret(self, client, settings):
        settings.ACMEPROXY_AUTHORISATION_CREATION_SECRETS = {
            "18084e750a1cff6f2d627e7a568ab81a": {"name": "developers"}
        }
        resp = client.post(
            "/create_authorisation",
            data={"name": "example.com", "secret": "18084e750a1cff6f2d627e7a568ab81a"},
        )
        assert resp.status_code == 200
        assert resp.json()["result"]["authorisation"] == "example.com"

    def test_create_authorisation_wrong_secret(self, client, settings):
        settings.ACMEPROXY_AUTHORISATION_CREATION_SECRETS = {
            "18084e750a1cff6f2d627e7a568ab81a": {"name": "developers"}
        }
        resp = client.post(
            "/create_authorisation",
            data={"name": "example.com", "secret": "wrong_secret"},
        )
        assert resp.status_code == 403
        assert resp.json()["result"] is False

    @pytest.mark.parametrize(
        "auth_settings,domain,secret,status_code",
        [
            (
                {"18084e750a1cff6f2d627e7a568ab81a": {"name": "developers"}},
                "example.com",
                "18084e750a1cff6f2d627e7a568ab81a",
                200,
            ),
            (
                {"18084e750a1cff6f2d627e7a568ab81a": {"name": "developers"}},
                "example.com",
                "wrong_secret",
                403,
            ),
            (
                {
                    "18084e750a1cff6f2d627e7a568ab81a": {
                        "name": "developers",
                        "permit": ["example.com"],
                    }
                },
                "example.com",
                "18084e750a1cff6f2d627e7a568ab81a",
                200,
            ),
            (
                {
                    "18084e750a1cff6f2d627e7a568ab81a": {
                        "name": "developers",
                        "permit": ["example.org"],
                    }
                },
                "example.com",
                "18084e750a1cff6f2d627e7a568ab81a",
                403,
            ),
            (
                {
                    "18084e750a1cff6f2d627e7a568ab81a": {
                        "name": "developers",
                        "permit": [".example.com"],
                    }
                },
                "example.com",
                "18084e750a1cff6f2d627e7a568ab81a",
                403,
            ),
            (
                {
                    "18084e750a1cff6f2d627e7a568ab81a": {
                        "name": "developers",
                        "permit": [".example.com"],
                    }
                },
                "test.example.com",
                "18084e750a1cff6f2d627e7a568ab81a",
                200,
            ),
            (
                {
                    "18084e750a1cff6f2d627e7a568ab81a": {
                        "name": "developers",
                        "permit": ["example.com"],
                    }
                },
                "test.example.com",
                "18084e750a1cff6f2d627e7a568ab81a",
                403,
            ),
        ],
    )
    def test_create_auth_permissions(
        self, client, settings, auth_settings, domain, secret, status_code
    ):
        settings.ACMEPROXY_AUTHORISATION_CREATION_SECRETS = auth_settings
        resp = client.post(
            "/create_authorisation", data={"name": domain, "secret": secret},
        )
        assert resp.status_code == status_code

    def test_expire_authorisation(self, client):
        Authorisation.objects.create(
            name="example.com", secret="test_secret", created_by_ip="127.0.0.1"
        )
        resp = client.post(
            "/expire_authorisation",
            data={"name": "example.com", "secret": "test_secret"},
        )
        assert resp.status_code == 200
        assert resp.json()["result"]["authorisation"] == "example.com"

    def test_expire_mixed_case(self, client):
        Authorisation.objects.create(
            name="example.com", secret="test_secret", created_by_ip="127.0.0.1"
        )
        resp = client.post(
            "/expire_authorisation",
            data={"name": "exAMplE.cOm", "secret": "test_secret"},
        )
        assert resp.status_code == 200
        assert resp.json()["result"]["authorisation"] == "example.com"

    def test_expire_wrong_secret(self, client):
        Authorisation.objects.create(
            name="example.com", secret="test_secret", created_by_ip="127.0.0.1"
        )
        resp = client.post(
            "/expire_authorisation",
            data={"name": "example.com", "secret": "wrong_secret"},
        )
        assert resp.status_code == 403
        assert resp.json()["result"] is False

    def test_expire_missing_name(self, client):
        Authorisation.objects.create(
            name="example.com", secret="test_secret", created_by_ip="127.0.0.1"
        )
        resp = client.post("/expire_authorisation", data={"secret": "test_secret"},)
        assert resp.status_code == 400
        assert resp.json()["result"] is False

    def test_expire_missing_secret(self, client):
        Authorisation.objects.create(
            name="example.com", secret="test_secret", created_by_ip="127.0.0.1"
        )
        resp = client.post("/expire_authorisation", data={"name": "example.com"},)
        assert resp.status_code == 400
        assert resp.json()["result"] is False

    def test_create_wrong_method(self, client):
        resp = client.get("/create_authorisation", data={"name": "example.com"})
        assert resp.status_code == 405

    def test_expire_wrong_method(self, client):
        resp = client.get("/expire_authorisation", data={"name": "example.com"})
        assert resp.status_code == 405


@pytest.mark.django_db
class TestResponse:
    def test_publish_response(self, client):
        Authorisation.objects.create(
            name="example.com", secret="test_secret", created_by_ip="127.0.0.1"
        )
        resp = client.post(
            "/publish_response",
            data={
                "name": "example.com",
                "response": "random_secret",
                "secret": "test_secret",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["result"]["authorisation"] == "example.com"
        assert resp.json()["result"]["published"] is True

    def test_publish_response_mixed_case(self, client):
        Authorisation.objects.create(
            name="example.com", secret="test_secret", created_by_ip="127.0.0.1"
        )
        resp = client.post(
            "/publish_response",
            data={
                "name": "exAMple.coM",
                "response": "random_secret",
                "secret": "test_secret",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["result"]["authorisation"] == "example.com"
        assert resp.json()["result"]["published"] is True

    def test_publish_wrong_secret(self, client):
        Authorisation.objects.create(
            name="example.com", secret="test_secret", created_by_ip="127.0.0.1"
        )
        resp = client.post(
            "/publish_response",
            data={
                "name": "example.com",
                "response": "random_secret",
                "secret": "wrong_secret",
            },
        )
        assert resp.status_code == 403
        assert resp.json()["result"] is False

    def test_publish_missing_name(self, client):
        Authorisation.objects.create(
            name="example.com", secret="test_secret", created_by_ip="127.0.0.1"
        )
        resp = client.post(
            "/publish_response",
            data={"response": "random_secret", "secret": "test_secret"},
        )
        assert resp.status_code == 400
        assert resp.json()["result"] is False

    def test_publish_missing_response(self, client):
        Authorisation.objects.create(
            name="example.com", secret="test_secret", created_by_ip="127.0.0.1"
        )
        resp = client.post(
            "/publish_response", data={"name": "example.com", "secret": "test_secret"},
        )
        assert resp.status_code == 400
        assert resp.json()["result"] is False

    def test_publish_missing_secret(self, client):
        Authorisation.objects.create(
            name="example.com", secret="test_secret", created_by_ip="127.0.0.1"
        )
        resp = client.post(
            "/publish_response",
            data={"name": "example.com", "response": "random_secret"},
        )
        assert resp.status_code == 400
        assert resp.json()["result"] is False

    def test_expire_response(self, client):
        Authorisation.objects.create(
            name="example.com", secret="test_secret", created_by_ip="127.0.0.1"
        )
        Response.objects.create(
            name="example.com", response="test_response", created_by_ip="127.0.0.1"
        )
        resp = client.post(
            "/expire_response", data={"name": "example.com", "secret": "test_secret"},
        )
        assert resp.status_code == 200
        assert resp.json()["result"]["authorisation"] == "example.com"

    def test_expire_response_mixed_case(self, client):
        Authorisation.objects.create(
            name="example.com", secret="test_secret", created_by_ip="127.0.0.1"
        )
        Response.objects.create(
            name="example.com", response="test_response", created_by_ip="127.0.0.1"
        )
        resp = client.post(
            "/expire_response", data={"name": "exAMple.Com", "secret": "test_secret"},
        )
        assert resp.status_code == 200
        assert resp.json()["result"]["authorisation"] == "example.com"

    def test_expire_missing_name(self, client):
        Authorisation.objects.create(
            name="example.com", secret="test_secret", created_by_ip="127.0.0.1"
        )
        Response.objects.create(
            name="example.com", response="test_response", created_by_ip="127.0.0.1"
        )
        resp = client.post("/expire_response", data={"secret": "test_secret"},)
        assert resp.status_code == 400
        assert resp.json()["result"] is False

    def test_expire_missing_secret(self, client):
        Authorisation.objects.create(
            name="example.com", secret="test_secret", created_by_ip="127.0.0.1"
        )
        Response.objects.create(
            name="example.com", response="test_response", created_by_ip="127.0.0.1"
        )
        resp = client.post("/expire_response", data={"name": "example.com"},)
        assert resp.status_code == 400
        assert resp.json()["result"] is False

    def test_expire_wrong_secret(self, client):
        Authorisation.objects.create(
            name="example.com", secret="test_secret", created_by_ip="127.0.0.1"
        )
        Response.objects.create(
            name="example.com", response="test_response", created_by_ip="127.0.0.1"
        )
        resp = client.post(
            "/expire_response", data={"name": "example.com", "secret": "wrong_secret"},
        )
        assert resp.status_code == 403
        assert resp.json()["result"] is False

    def test_publish_wrong_method(self, client):
        resp = client.get("/publish_response", data={"name": "example.com"})
        assert resp.status_code == 405

    def test_expire_wrong_method(self, client):
        resp = client.get("/expire_response", data={"name": "example.com"})
        assert resp.status_code == 405
