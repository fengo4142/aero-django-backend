#!/bin/bash
set -e

STAGE="dev"
APPNAME="aeros"
ID="us"
REGION="us-east-1"
OPTS=$*

while [ -n "$1" ]; do # while loop starts
    case "$1" in
    --stage)
        STAGE="$2"
        shift
        ;;
    --appname)
        APPNAME="$2"
        shift
        ;;
    --region)
        REGION="$2"
        shift
        ;;
    --id)
        ID="$2"
        shift
        ;;
    --)
        shift # The double dash makes them parameters
        break
        ;;
    *)  ;;
    esac
    shift
done
total=1
for param in "$@"; do
    echo "#$total: $param"
    total=$(($total + 1))
done

DIR=`dirname "${BASH_SOURCE[0]}"`
DIR=$DIR/..
ENDPOINT="db.${ID}.${STAGE}.aerosimple.com"
#ENDPOINT=127.0.0.1
EMPTY=""
EP="Endpoint: "
PROD="prod."
export PROJECT_DATABASE_HOST="${ENDPOINT/$PROD/$EMPTY}"
export PROJECT_DATABASE_NAME=aerosimple
export PROJECT_DATABASE_USERNAME=$PROJECT_DATABASE_NAME
export PROJECT_DATABASE_PASSWORD=${DB_PASSWORD:-Aerosimple}
echo $PROJECT_DATABASE_HOST
virtualenv $DIR/venv --python=python3.7
source $DIR/venv/bin/activate
pip install -r $DIR/requirements.txt
$DIR/manage.py migrate
# Create an admin when deploying for the first time
echo "from django.contrib.auth.models import User; import os; User.objects.create_superuser('admin', 'admin@unosimple.com', os.environ.get('DJANGO_ADMIN_PASSWORD','admin123')) if len(User.objects.filter(email='admin@unosimple.com')) == 0 else print('Admin exists')"|$DIR/manage.py shell
# We need the so, Lambda env does not contaon it.
cd $DIR
# cp ./scripts/_sqlite3.so .
# sls deploy $OPTS
# rm _sqlite3.so
