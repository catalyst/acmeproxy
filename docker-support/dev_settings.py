import os

from acmeproxy.acmeproxy import settings  # noqa: F401
from acmeproxy.acmeproxy.settings import *  # noqa: F401, F403

SECRET_KEY = "this key is very hush hush!"
DEBUG = True


def filter_werkzeug_request_logging(record):
    """Werkzeug wants to log all requests, but we already do that"""
    if isinstance(record.msg, str):
        # This is a bit of a gross way to filter
        return ' HTTP/1.0\u001b[0m" ' not in record.msg
    return True


STATIC_ROOT = "/static"

AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]


EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
