import os

## Configuration to change when deploying acmeproxy

LANGUAGE_CODE = 'en-nz'
TIME_ZONE = 'Pacific/Auckland'
SECRET_KEY = 'set this to something random (e.g. dd if=/dev/urandom bs=1 count=16 | xxd -ps)'
ALLOWED_HOSTS = []

ACMEPROXY_SOA_HOSTNAME = 'acme-proxy-ns1.example.com'
ACMEPROXY_SOA_CONTACT = 'hostmaster.example.com'

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

## Django settings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'proxy',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'acmeproxy.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'acmeproxy.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/


USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
