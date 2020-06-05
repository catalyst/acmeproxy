FROM buildpack-deps:bionic

# Install the build dependencies and prime the cache
RUN set -ex \
    && apt-get update \
    && apt-get install --no-install-recommends --no-install-suggests --quiet --yes --verbose-versions \
        build-essential \
        gettext \
        libldap2-dev \
        libsasl2-dev \
        libssl-dev \
        libpq5 \
        python3 \
        python3-dev \
        python3-pip \
        python3-setuptools \
        python3-venv \
        python3-wheel \
    && rm -rf /var/lib/apt/lists/ \
    && apt-get autoremove --purge --quiet --yes \
    && apt-get purge --quiet --yes \
    && apt-get clean \
    && pip3 install --upgrade \
        pip \
        setuptools  \
        dumb-init \
        wheel \
    && rm -rf /root/.cache/pip

ARG MAXMIND_LICENSE_KEY

RUN set -ex \
    && python3 -m venv /venv \
    && /venv/bin/pip install --upgrade \
        pip \
        pipenv \
        setuptools  \
        wheel

COPY Pipfile.lock ./docker-support/pipfile-to-requirements.py /
RUN set -ex \
    && python3 /pipfile-to-requirements.py /Pipfile.lock > /tmp/requirements.txt \
    && pip3 download --dest=/tmp --requirement /tmp/requirements.txt \
    && rm -rf /tmp /pipfile-to-requirements.py /Pipfile.lock

COPY ./ /code/

ENV VIRTUAL_ENV=/venv \
    PATH=/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONWARNINGS=always \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

RUN set -ex \
    && cd /code \
    && PYTHONWARNINGS= pip install --exists-action=w \
        -e . \
    && PYTHONWARNINGS= pipenv sync --dev \
    && ln -s /tiaki_settings.py "$(python -c 'from distutils.sysconfig import get_python_lib; print(get_python_lib())')/tiaki_settings.py"

ENTRYPOINT ["/usr/local/bin/dumb-init"]

ENV DJANGO_SETTINGS_MODULE tiaki_settings
EXPOSE 8080
