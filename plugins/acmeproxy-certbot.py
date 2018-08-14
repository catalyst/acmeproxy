#!/usr/bin/python3

"""
acmeproxy dns-01 hook for <https://certbot.eff.org/>
Michael Fincham <michael.fincham@catalyst.net.nz>

Usage
-----

Create a cli.ini for certbot in /etc/letsencrypt/cli.ini:

  rsa-key-size = 4096
  preferred-challenges = dns
  manual-auth-hook = /opt/acmeproxy/acmeproxy-certbot.py auth
  manual-cleanup-hook = /opt/acmeproxy/acmeproxy-certbot.py cleanup
  manual-public-ip-logging-ok = True

And create a configuration file in /etc/acmeproxy.ini:

  [defaults]
  endpoint=https://acme-proxy-ns1.example.com

  [domain:example.org]
  secret=786575b19e29abcad093c8af793a4e2b
  
  [domain:example.net]
  secret=f3073e829c8b4dc40e906f084069d75c

Make sure the acmeproxy.ini file isn't world readable, then run certbot
with the options necessary in your environment, e.g.

  certbot  --manual --installer=apache
"""

import argparse
import configparser
import os
import stat
import sys

import requests

class AcmeproxyClient(object):
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
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--configuration-path', metavar="PATH", type=str, default="/etc/acmeproxy.ini", help="path to the configuration file, defaults to /etc/acmeproxy.ini")
    parser.add_argument('hook', metavar="HOOK", type=str, help="hook to execute, either auth or cleanup")
    args = parser.parse_args()
    config = configparser.ConfigParser()

    try:
        try:
            if os.stat(args.configuration_path).st_mode & stat.S_IROTH:
                sys.stderr.write("error: configuration is world readable, fix the file permissions and re-create exposed keys")
                sys.exit(1)
        except FileNotFoundError:
            sys.stderr.write("error: configuration file '%s' does not exist\n" % args.configuration_path)
            sys.exit(1)
        else:
            if not os.access(args.configuration_path, os.R_OK):
                raise
            config.read(args.configuration_path)
    except:
        sys.stderr.write("error: unable to read the configuration file from '%s'\n" % args.configuration_path)
        sys.exit(1)

    try:
        domain = os.environ['CERTBOT_DOMAIN'].lower()
        challenge = os.environ['CERTBOT_VALIDATION']
    except:
        sys.stderr.write("error: CERTBOT_DOMAIN and CERTBOT_VALIDATION must be set in the environment\n")
        sys.exit(1)

    section_pattern = "domain:"
    all_domain_metadata = {}
    for section in config.sections():
        if not section.lower().startswith(section_pattern):
            continue
        section_domain = section[len(section_pattern):].lower()
        all_domain_metadata[section_domain] = {
            'endpoint': config[section].get('endpoint', config.get('defaults', 'endpoint', fallback=None)),
            'secret': config[section].get('secret', config.get('defaults', 'secret', fallback=None))
        }

    if domain not in all_domain_metadata:
        sys.stderr.write("error: domain '%s' not found in configuration file\n" % domain)
        sys.exit(1)

    domain_metadata = all_domain_metadata[domain]
    if domain_metadata['secret'] is None or domain_metadata['endpoint'] is None:
        sys.stderr.write("error: domain '%s' is missing required configuration, 'endpoint' and 'secret' must be configured\n" % domain)
        sys.exit(1)

    client = AcmeproxyClient(domain_metadata['endpoint'], domain_metadata['secret'], domain, challenge) 

    if args.hook == 'auth':
        client.publish_record(challenge)
    elif args.hook == 'cleanup':
        client.delete_record()
    else:
        sys.stderr.write("error: unhandled hook '%s'\n" % hook)
        sys.exit(2)
