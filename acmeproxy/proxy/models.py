from datetime import timedelta

from django.db import models
from django.utils import timezone

from .utils import generate_secret


class Account(models.Model):
    name = models.CharField(max_length=255)
    secret = models.CharField(max_length=128, unique=True, default=generate_secret)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    created_by_ip = models.GenericIPAddressField(verbose_name="Created by IP address")
    permit_domains = models.TextField(verbose_name="Permitted domains",
        help_text="Comma separated list of domains the account is allowed to obtain authorisations for.\
            For example: example.com, .example.com, www.example.org")
    notes = models.CharField(max_length=255, null=True, blank=True,
        help_text="Any applicable notes for the account, such as WR.")

    def __str__(self):
        return self.name


class Authorisation(models.Model):
    name = models.CharField(max_length=255)
    secret = models.CharField(max_length=128, unique=True, default=generate_secret)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    created_by_ip = models.GenericIPAddressField(verbose_name="Created by IP address")
    account = models.ForeignKey('Account', on_delete=models.CASCADE, default=0)

    def __str__(self):
        return self.name

    def reset_secret(self):
        self.secret = generate_secret()


class Response(models.Model):
    name = models.CharField(max_length=255)
    response = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    created_by_ip = models.GenericIPAddressField(verbose_name="Created by IP address")
    expired_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return "_acme-challenge.%s IN TXT %s" % (self.name, self.response)

    def live(self):
        threshold = timezone.now() - timedelta(minutes=5)
        return self.created_at > threshold and (
            self.expired_at is None or self.expired_at > timezone.now()
        )

    live.boolean = True
