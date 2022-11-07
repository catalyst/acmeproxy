from acmeproxy.acmeproxy import settings  # noqa: F401
from acmeproxy.acmeproxy.settings import *  # noqa: F401, F403

## Configuration to change when deploying acmeproxy

LANGUAGE_CODE = "en-nz"
TIME_ZONE = "Pacific/Auckland"
SECRET_KEY = (
    "set this to something random (e.g. pwgen -sy 50 1)"
)
ALLOWED_HOSTS = []

ACMEPROXY_SOA_HOSTNAME = "acme-proxy-ns1.example.com"
ACMEPROXY_SOA_CONTACT = "hostmaster.example.com"
