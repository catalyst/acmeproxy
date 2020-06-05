#!/usr/bin/env bash
set -ex

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

django-admin --version

# django-admin collectstatic --no-input

django-admin migrate

# Try to load fixtures, ignore failures
django-admin loaddata "${DIR}"/fixtures/* || true

# Ensure that the log file permissions are correct and that the file is empty
chown -R --reference=/code/Dockerfile /logs
true > /logs/json.log

django-admin runserver 0.0.0.0:8080
