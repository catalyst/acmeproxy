import os
import binascii


# stolen from https://stackoverflow.com/a/4581997
def client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


# generate a random 128 bit secret
# this doesn't check that secret is unique in the applicable table
def generate_secret():
    return binascii.hexlify(os.urandom(16)).decode("cp437")
