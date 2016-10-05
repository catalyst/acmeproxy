# acmeproxy

This PowerDNS backend only serves [ACME dns-01 challenge responses](https://tools.ietf.org/html/draft-ietf-acme-acme-01), and exposes an HTTPS API to permit those challenge responses to be published by automated certificate renewal tools.

## Use with dehydrated

An example [dehydrated](http://dehydrated.de/) plugin is supplied in the `plugins` directory. Edit this plugin to specify the location of your acmeproxy installation and authorisation key registered with the API, then call it as a dns-01 hook.

    dehydrated -c -t dns-01 -k ./acmeproxy-dehydrated.sh -d secure.example.com

## Deployment

PowerDNS requires that the `Content-Length` header be present in backend responses, so a reverse proxy such as Apache is required. 

### Example Apache w/ certbot configuration

    <VirtualHost *:80>
      DocumentRoot /var/www/html

      ErrorLog ${APACHE_LOG_DIR}/error.log
      CustomLog ${APACHE_LOG_DIR}/access.log combined

      ProxyPass / http://127.0.0.1:8000/
      ProxyPassReverse / http://127.0.0.1:8000/

      RewriteEngine on
      RewriteCond %{SERVER_NAME} =acme-proxy-ns1.example.com
      RewriteCond %{REMOTE_ADDR} !^127\.0\.0\.1$
      RewriteRule ^ https://%{SERVER_NAME}%{REQUEST_URI} [END,QSA,R=permanent]
    </VirtualHost>
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

      SSLCertificateFile /etc/letsencrypt/live/cat-prod-acmeproxyns1.catalyst.net.nz/fullchain.pem
      SSLCertificateKeyFile /etc/letsencrypt/live/cat-prod-acmeproxyns1.catalyst.net.nz/privkey.pem 
      Include /etc/letsencrypt/options-ssl-apache.conf
    </VirtualHost>

### Example PowerDNS configuration

#### /etc/powerdns/pdns.conf

    config-dir=/etc/powerdns
    include-dir=/etc/powerdns/pdns.d
    security-poll-suffix=
    setgid=pdns
    setuid=pdns

#### /etc/powerdns/pdns.d/acmeproxy.conf

    launch=remote
    remote-connection-string=http:url=http://127.0.0.1/dns,url-suffix=,timeout=2000

## API documentation

### HTTPS API usage

All API endpoints will return JSON containing a `result` key describing the result of the operation. If an operation fails this will be `false`, and the HTTP response code will indicate the nature of the failure.

#### Authorisations

Before delegating any names an **authorisation** should be requested using the `create_authorisation` endpoint.

    $ curl --data "name=secure.example.com&suffix_match=false" https://acme-proxy-ns1.example.com/create_authorisation
    {"result": {"secret": "52f562aedc99383c6af848bc7016380a", "authorisation": "secure.example.com", "suffix_match": false}}

The randomly generated `secret` is then used to identify this authorisation in further calls to the API.

For cases where you would like an authorisation for `example.com` to be able to issue certificates for all names under `example.com` (e.g. `secure.example.com`) without explicit configuration, set `suffix_match` to `true`.

To re-generate the authentication secret for a given authorisation the `expire_authorisation` endpoint may be used.

    $ curl --data "name=secure.example.com&secret=52f562aedc99383c6af848bc7016380a" https://acme-proxy-ns1.example.com/expire_authorisation
    {"result": {"secret": "e04541b1d63bc68d296137bc2ee86923", "authorisation": "secure.example.com", "suffix_match": false}}

#### Challenge responses

During an ACME dns-01 challenge it is necessary to publish a **challenge response** string supplied by the ACME client. The `publish_response` endpoint allows a response to be published for a name that has been registered with an authorisation.

    $ curl --data "name=secure.example.com&response=evaGxfADs6pSRb2LAv9IZf17Dt3juxGJ-PCt92wr-oA&secret=52f562aedc99383c6af848bc7016380a" https://acme-proxy-ns1.example.com/publish_response
    {"result": {"authorisation": "example.com", "suffix_match": true, "published": true}}

Optionally a client may request that all challenge responses for a name be expired once they are no longer required, however the backend will expire them regardless after five minutes.

    $ curl --data "name=secure.example.com&secret=52f562aedc99383c6af848bc7016380a" https://acme-proxy-ns1.example.com/expire_response
    {"result": {"authorisation": "example.com", "suffix_match": true, "expired": true}}

### DNS usage

Suppose you have a domain `example.com` and wish to issue certificates for `secure.example.com` without having an HTTP server running and without giving full control of the `example.com` zone to an ACME client.

By registering an authorisation through the HTTPS API then adding a delegation for the expected challenge, `_acme-challenge.secure.example.com` it is possible to response to those challenges with data supplied using an HTTPS POST to the server.

    _acme-challenge.secure.example.com. IN NS acme-proxy-ns1.example.com
    
It should also be possible to load this backend along side your existing backends, though that functionality is not yet fully tested.

Once the delegation is made a response can be published using the `publish_response` endpoint of the HTTPS API during ACME certification issuance.

## Caveats

Presently there is no access control on who may register a new authorisation. This will be added in a future release. 
