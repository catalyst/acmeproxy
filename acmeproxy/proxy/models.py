from datetime import timedelta
import binascii
import os

from django.contrib.auth.hashers import make_password
from django.db import models
from django.utils import timezone

class Authorisation(models.Model):
    name = models.CharField(max_length=255)
    suffix_match = models.BooleanField()
    secret = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    created_by_ip = models.GenericIPAddressField(verbose_name="Created by IP address")
    
    class Meta:
        unique_together = ('name', 'suffix_match')

    def __str__(self):
        return(self.name)

    def reset_secret(self):
        self.secret = binascii.hexlify(os.urandom(16)).decode('cp437') # generate a random 128 bit secret

class Response(models.Model):
    name = models.CharField(max_length=255)
    response = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    created_by_ip = models.GenericIPAddressField(verbose_name="Created by IP address")
    expired_at = models.DateTimeField(null=True)

    def __str__(self):
        return("_acme-challenge.%s IN TXT %s" % (self.name, self.response))

    def live(self):
        threshold = timezone.now() - timedelta(minutes=5)
        return(self.created_at > threshold)
    live.boolean = True

