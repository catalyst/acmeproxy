#!/usr/bin/env bash
set -ex

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

django-admin --version

django-admin migrate

django-admin runserver 0.0.0.0:8080
