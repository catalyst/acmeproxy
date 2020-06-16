from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from acmeproxy.proxy.models import Authorisation, Response


@pytest.mark.django_db
class TestDeleteAuthorisation:
    def test_successful_delete(self):
        Authorisation.objects.create(
            name="example.com", secret="test_secret", created_by_ip="127.0.0.1"
        )
        out = StringIO()
        call_command("deleteauthorisation", "example.com", stdout=out)
        assert Authorisation.objects.count() == 0

    def test_different_name(self):
        Authorisation.objects.create(
            name="example.com", secret="test_secret", created_by_ip="127.0.0.1"
        )
        out = StringIO()
        with pytest.raises(CommandError):
            call_command("deleteauthorisation", "example.org", stdout=out)

    def test_mixed_case(self):
        Authorisation.objects.create(
            name="example.com", secret="test_secret", created_by_ip="127.0.0.1"
        )
        out = StringIO()
        call_command("deleteauthorisation", "eXAmple.cOm", stdout=out)
        assert Authorisation.objects.count() == 0


@pytest.mark.django_db
class TestListAuthorisations:
    def test_successful_list(self):
        Authorisation.objects.create(
            name="example.com", secret="test_secret", created_by_ip="127.0.0.1"
        )
        out = StringIO()
        call_command("listauthorisations", stdout=out)
        assert "example.com" in out.getvalue()

    def test_nothing(self):
        out = StringIO()
        with pytest.raises(CommandError):
            call_command("listauthorisations", stdout=out)


@pytest.mark.django_db
class TestListResponses:
    def test_successful_list(self):
        Authorisation.objects.create(
            name="example.com", secret="test_secret", created_by_ip="127.0.0.1"
        )
        Response.objects.create(
            name="example.com", response="test_response", created_by_ip="127.0.0.1"
        )
        out = StringIO()
        call_command("listresponses", stdout=out)
        assert "example.com" in out.getvalue()

    def test_nothing(self):
        out = StringIO()
        with pytest.raises(CommandError):
            call_command("listresponses", stdout=out)


@pytest.mark.django_db
class TestPipeAPI:
    @pytest.mark.parametrize(
        "test_input, output",
        [
            ("HELO\t1\nDEBUGQUIT", "OK\tACME Proxy API\n"),
            (
                "HELO\t1\nQ\texample.com\th\tANY\th\t127.0.0.1\nDEBUGQUIT",
                'OK\tACME Proxy API\nDATA\texample.com\tIN\tSOA\t5\t1\tacme-proxy-ns1.example.com. hostmaster.example.com. 1592267735 0 0 0 0\nDATA\texample.com\tIN\tNS\t5\t1\tacme-proxy-ns1.example.com\nDATA\texample.com\tIN\tCAA	5\t1\t0 issue "letsencrypt.org"\nEND\n',
            ),
            (
                "HELO\t1\nQ\texample.com\th\tCAA\th\t127.0.0.1\nDEBUGQUIT",
                'OK\tACME Proxy API\nDATA\texample.com\tIN\tCAA	5\t1\t0 issue "letsencrypt.org"\nEND\n',
            ),
            (
                "HELO\t1\nQ\t_acme-challenge.example.com\th\tANY\th\t127.0.0.1\nDEBUGQUIT",
                'OK\tACME Proxy API\nDATA\t_acme-challenge.example.com	IN\tTXT	5\t1\ttest_response\nDATA\t_acme-challenge.example.com\tIN\tSOA\t5\t1\tacme-proxy-ns1.example.com. hostmaster.example.com. 1592267735 0 0 0 0\nDATA\t_acme-challenge.example.com\tIN\tNS\t5\t1\tacme-proxy-ns1.example.com\nDATA\t_acme-challenge.example.com\tIN\tCAA	5\t1\t0 issue "letsencrypt.org"\nEND\n',
            ),
            (
                "HELO\t1\nQ\t_acme-challenge.example.com\th\tTXT\th\t127.0.0.1\nDEBUGQUIT",
                "OK\tACME Proxy API\nDATA\t_acme-challenge.example.com	IN\tTXT	5\t1\ttest_response\nEND\n",
            ),
            ("RANDOM GARBAGE", "FAIL\n",),
            ("RANDOMGARBAGE", "FAIL\n",),
            ("HELO\t1\nRANDOMGARBAGE\nDEBUGQUIT", "OK\tACME Proxy API\n",),
            (
                "HELO\t1\nR random correct number of things\nDEBUGQUIT",
                "OK\tACME Proxy API\nEND\n",
            ),
            (
                "HELO\t1\nRANDOMGARBAGE\nQ\texample.com\th\tCAA\th\t127.0.0.1\nDEBUGQUIT",
                'OK\tACME Proxy API\nDATA\texample.com\tIN\tCAA	5\t1\t0 issue "letsencrypt.org"\nEND\n',
            ),
            (
                "HELO\t1\nR random correct number of things\nQ\texample.com\th\tCAA\th\t127.0.0.1\nDEBUGQUIT",
                'OK\tACME Proxy API\nEND\nDATA\texample.com\tIN\tCAA	5\t1\t0 issue "letsencrypt.org"\nEND\n',
            ),
        ],
    )
    def test_query(self, monkeypatch, test_input, output):
        Authorisation.objects.create(
            name="example.com", secret="test_secret", created_by_ip="127.0.0.1"
        )
        Response.objects.create(
            name="example.com", response="test_response", created_by_ip="127.0.0.1"
        )
        out = StringIO()
        monkeypatch.setattr(
            "sys.stdin", StringIO(test_input),
        )
        monkeypatch.setattr("time.time", lambda: 1592267735)
        with pytest.raises(SystemExit):
            call_command("pipeapi", stdout=out)
        assert out.getvalue() == output
