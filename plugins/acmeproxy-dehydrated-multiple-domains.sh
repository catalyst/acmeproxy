#!/bin/bash

# acmeproxy dns-01 hook for <http://dehydrated.de/>
# Michael Fincham <michael.fincham@catalyst.net.nz>
# Grant McLean <grant@catalyst.net.nz>
#
# This example hook looks up mappings between domain names and their respective authorisation keys in 
# a file (for instance, /etc/acmeproxy-keys). The file should have a line format like:
#
# example.com 0ceefa693a2e8ca6fa4fa33570d9cda3
#
# Where each domain is followed by whitespace and then the domain's authorisation key.
#
# Usage:
# dehydrated -c -t dns-01 -k ./acmeproxy-dehydrated-multiple-domains.sh -d example.com

endpoint=https://acme-proxy-ns1.example.com
secret=$(awk "\$1 == \"${2}\" {print \$2}" /etc/acmeproxy-keys)
if [ -n "${2}" -a -z "${secret}" ]; then
    echo "No secret key for host '$2'"
    exit 1
fi

case ${1} in
    deploy_challenge)
        echo " + Publishing challenge for ${2} to ${endpoint}..."
        if curl --silent --data "secret=${secret}&name=${2}&response=${4}" ${endpoint}/publish_response | grep 'published' >/dev/null 2>&1; then
            echo " + Published successfully!"
        else
            echo "ERROR: Could not publish challenge."
            exit 1
        fi
    ;;
    clean_challenge)
        echo " + Expiring challenges for ${2} at ${endpoint}..."
        if curl --silent --data "secret=${secret}&name=${2}" ${endpoint}/expire_response | grep 'expired' >/dev/null 2>&1; then
            echo " + Expired successfully!"
        else
            echo "ERROR: Could not expire challenges."
            exit 1
        fi
    ;;
    deploy_cert)
        echo " + This DNS hook cannot deploy certificates. Certificate will need to be manually deployed!"
    ;;
    startup_hook)
    ;;
    exit_hook)
    ;;
    *_cert)
    ;;
    *)
        echo "dehydrated requested an unknown hook action: ${1}"
    ;;
esac
