from acmeproxy.acmeproxy import settings  # noqa: F401
from acmeproxy.acmeproxy.settings import *  # noqa: F401, F403

SECRET_KEY = "this key is very hush hush!"
DEBUG = True

ACMEPROXY_SOA_HOSTNAME = "acme-proxy-ns1.example.com"
ACMEPROXY_SOA_CONTACT = "hostmaster.example.com"

ACMEPROXY_AUTHORISATION_CREATION_SECRETS = None
