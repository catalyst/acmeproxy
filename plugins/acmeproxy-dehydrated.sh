#!/bin/bash

# acmeproxy dns-01 hook for <http://dehydrated.de/>
# Michael Fincham <michael.fincham@catalyst.net.nz>
#
# Usage:
# dehydrated -c -t dns-01 -k ./acmeproxy-dehydrated.sh -d example.com

endpoint=https://acme-proxy-ns1.example.com
secret=52f562aedc99383c6af848bc7016380a

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
        echo "letsencrypt.sh requested an unknown hook action: ${1}"
    ;;
esac
