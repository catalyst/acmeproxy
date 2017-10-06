#!/usr/bin/python3
#
# acmeproxy dns-01 hook for <https://certbot.eff.org/>
# Michael Fincham <michael.fincham@catalyst.net.nz>
#
# Usage:
#
# Modify the script to point to your local ACMEproxy instance, then create a
# cli.ini for certbot, for instance in /etc/letsencrypt/cli.ini:
#
# rsa-key-size = 4096
# preferred-challenges = dns
# manual-auth-hook = /opt/acmeproxy/acmeproxy-certbot.py auth
# manual-cleanup-hook = /opt/acmeproxy/acmeproxy-certbot.py cleanup
# manual-public-ip-logging-ok = True
#
# Then run certbot like:
#
# certbot  --manual --installer=apache

import json
import os
import sys
import time

import requests

class AcmeproxyHook(object):
    def __init__(self, endpoint, secret, domain, challenge):
        self.endpoint = endpoint
        self.secret = secret
        self.domain = domain
        self.challenge = challenge

    def publish_record(self, challenge):
        print(requests.post("%s/publish_response" % (self.endpoint, ), data = {'name':self.domain, 'secret': self.secret, 'response': self.challenge}).text)

    def delete_record(self):
        print(requests.post("%s/expire_response" % (self.endpoint, ), data = {'name':self.domain, 'secret': self.secret}).text)

if __name__ == "__main__":
    try:
        hook = sys.argv[1]
        domain = os.environ['CERTBOT_DOMAIN'].lower()
        challenge = os.environ['CERTBOT_VALIDATION']
    except:
        sys.stderr.write("error: CERTBOT_DOMAIN and CERTBOT_VALIDATION must be set in the environment\nand a hook (auth, cleanup) must be specified as an argument. giving up.\n")
        sys.exit(1)

    client = AcmeproxyHook("https://acme-proxy-ns1.example.com", "b961a494cc0885f2991e7989819e6bf6", domain, challenge)

    if hook == 'auth':
        client.publish_record(challenge)
    elif hook == 'cleanup':
        client.delete_record()
    else:
        sys.stderr.write("error: unhandled hook `%s'. giving up.\n" % hook)
        sys.exit(2)
