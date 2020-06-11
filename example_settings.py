from acmeproxy.acmeproxy import settings  # noqa: F401
from acmeproxy.acmeproxy.settings import *  # noqa: F401, F403

## Configuration to change when deploying acmeproxy

LANGUAGE_CODE = "en-nz"
TIME_ZONE = "Pacific/Auckland"
SECRET_KEY = (
    "set this to something random (e.g. dd if=/dev/urandom bs=1 count=16 | xxd -ps)"
)
ALLOWED_HOSTS = []

ACMEPROXY_SOA_HOSTNAME = "acme-proxy-ns1.example.com"
ACMEPROXY_SOA_CONTACT = "hostmaster.example.com"

# if this is None then no authentication is required to request an authorisation for a name
ACMEPROXY_AUTHORISATION_CREATION_SECRETS = None

# otherwise you can set up API keys like so...
#
# ACMEPROXY_AUTHORISATION_CREATION_SECRETS = {
#     'dbb62ae39642b9d2e81ee7a5e5e8d175': {
#         'name': 'operations-team',
#         'permit': ['example.com', '.example.org'], <--- optional list of valid names
#     }
#     '18084e750a1cff6f2d627e7a568ab81a': {
#         'name': 'developers',
#     }
# }
