# acmeproxy

This PowerDNS backend only serves [ACME dns-01 challenge responses](https://letsencrypt.org/docs/acme-protocol-updates/), and exposes an HTTPS API to permit those challenge responses to be published by automated certificate renewal tools.

## Dev environment

You can start a dev environemnt with

    docker-compose up

The app will now be available at http://localhost:8080

## Use with dehydrated or certbot

Example plugins for [dehydrated](http://dehydrated.de/) and [certbot](https://certbot.eff.org/) are supplied in the `plugins` directory. Edit these plugin to specify the location of your acmeproxy installation and authorisation key registered with the API, then call them as a dns-01 hook.

For instance, with dehydrated:

    dehydrated -c -t dns-01 -k ./acmeproxy-dehydrated.sh -d secure.example.com

## Deployment

Install the app in a virtual environemnt with

    pip install .

In a new directory make  a copy of `example_settings.py` called `acmeproxy_settings.py`. Then fill in all the values.

With your working directory set as the newly created directory you can now run the app as a wsgi app. With the environment variable `DJANGO_SETTINGS_MODULE` set to `acmeproxy_settings`. and the wsgi app at `acmeproxy.acmeproxy.wsgi:application`.

### Example Apache configuration when certbot is used for the API certificate

    <VirtualHost *:443>
      ServerName acme-proxy-ns1.example.com
      DocumentRoot /var/www/html

      ErrorLog ${APACHE_LOG_DIR}/error.log
      CustomLog ${APACHE_LOG_DIR}/access.log combined

      ProxyPass / http://127.0.0.1:8000/
      ProxyPassReverse / http://127.0.0.1:8000/

      <Location /admin>
          Require ip 127.0.0.1
      </Location>

      SSLCertificateFile /etc/letsencrypt/live/acme-proxy-ns1.example.com/fullchain.pem
      SSLCertificateKeyFile /etc/letsencrypt/live/acme-proxy-ns1.example.com/privkey.pem
      Include /etc/letsencrypt/options-ssl-apache.conf
    </VirtualHost>

### Example PowerDNS configuration

In the directory with your settings file make a new file called `backend`.

In it put

    #!/bin/sh
    export DJANGO_SETTINGS_MODULE=acmeproxy_settings
    /path/to/venv/django-admin pipeapi

#### /etc/powerdns/pdns.conf

    config-dir=/etc/powerdns
    include-dir=/etc/powerdns/pdns.d
    setgid=pdns
    setuid=pdns

#### /etc/powerdns/pdns.d/acmeproxy.conf

    launch=pipe
    pipe-command=/opt/acmeproxy/backend
    pipe-timeout=4000

## API documentation

### HTTPS API usage

All API endpoints will return JSON containing a `result` key describing the result of the operation. If an operation fails this will be `false`, and the HTTP response code will indicate the nature of the failure.

#### Authorisations

Before delegating any names an **authorisation** should be requested using the `create_authorisation` endpoint.

    $ curl --data "name=secure.example.com" https://acme-proxy-ns1.example.com/create_authorisation
    {"result": {"secret": "52f562aedc99383c6af848bc7016380a", "authorisation": "secure.example.com", "suffix_match": false}}

If authentication is enabled in your installation (with the `ACMEPROXY_AUTHORISATION_CREATION_SECRETS` setting configured to something other than `None`) you will also need to supply a `secret` field corresponding to the account being used.

The randomly generated `secret` returned by this call is then used to identify this authorisation in further calls to the API.

To re-generate the authentication secret for a given authorisation the `expire_authorisation` endpoint may be used.

    $ curl --data "name=secure.example.com&secret=52f562aedc99383c6af848bc7016380a" https://acme-proxy-ns1.example.com/expire_authorisation
    {"result": {"secret": "e04541b1d63bc68d296137bc2ee86923", "authorisation": "secure.example.com", "suffix_match": false}}

#### Challenge responses

During an ACME dns-01 challenge it is necessary to publish a **challenge response** string supplied by the ACME client. The `publish_response` endpoint allows a response to be published for a name that has been registered with an authorisation.

    $ curl --data "name=secure.example.com&response=evaGxfADs6pSRb2LAv9IZf17Dt3juxGJ-PCt92wr-oA&secret=52f562aedc99383c6af848bc7016380a" https://acme-proxy-ns1.example.com/publish_response
    {"result": {"authorisation": "secure.example.com", "suffix_match": false, "published": true}}

Optionally a client may request that all challenge responses for a name be expired once they are no longer required, however the backend will expire them regardless after five minutes.

    $ curl --data "name=secure.example.com&secret=52f562aedc99383c6af848bc7016380a" https://acme-proxy-ns1.example.com/expire_response
    {"result": {"authorisation": "secure.example.com", "suffix_match": false, "expired": true}}

### DNS usage

Suppose you have a domain `example.com` and wish to issue certificates for `secure.example.com` without having an HTTP server running and without giving full control of the `example.com` zone to an ACME client.

By registering an authorisation through the HTTPS API then adding a delegation for the expected challenge, `_acme-challenge.secure.example.com` it is possible to response to those challenges with data supplied using an HTTPS POST to the server.

    _acme-challenge.secure.example.com. IN NS acme-proxy-ns1.example.com

It should also be possible to load this backend along side your existing backends, though that functionality is not yet fully tested.

Once the delegation is made a response can be published using the `publish_response` endpoint of the HTTPS API during ACME certification issuance.

### Command line tools

There are several Django management commands available in the `proxy` app.

#### listauthorisations 

Lists all authorisations present in the database.

    $ python manage.py listauthorisations
    name                   created_by_ip    created_at                        account
    ---------------------  ---------------  --------------------------------  ---------
    secure.example.com     192.0.2.1        2016-10-10 03:11:18.525111+00:00  operations
    test.example.org       192.0.2.1        2016-10-10 03:50:35.827334+00:00  test
    host1.example.com      192.0.2.1        2016-10-10 03:51:38.185688+00:00  operations

#### deleteauthorisation

Permanently remove an authorisation from the database.

    $ python manage.py deleteauthorisation test.example.org
    Successfully deleted authorisation "test.example.org"

#### listresponses

List the audit log of challenge responses that have been published, optionally between any two dates.

    $ python manage.py listresponses --start=2016-09-01 --end=2016-12-30
    name                 expired_at                        created_by_ip    created_at
    -------------------  --------------------------------  ---------------  --------------------------------
    secure.example.com   2016-10-10 03:12:05.984890+00:00  192.0.2.1        2016-10-09 21:47:24.236299+00:00
    test.example.org     2016-10-10 03:12:05.984890+00:00  192.0.2.1        2016-10-10 03:12:04.833764+00:00

A response will have an `expired_at` value if the ACME client explicitly marked all challenges for a name as complete.

