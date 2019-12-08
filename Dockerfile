# FROM registry.gitlab.com/aerosimple/docker-public-images/python-dev:latest
FROM python:3.7

RUN pip3 install --upgrade pip

VOLUME ["/usr/development/app","/usr/development/media"]

WORKDIR /usr/development/app

EXPOSE 8000

# You should set the DJANGO_SETTINGS_MODULE to the appropiate django file
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]

RUN apt-get update && apt-get install -y \
    gdal-bin gettext

COPY requirements.txt /usr/development/
RUN pip3 install -r /usr/development/requirements.txt
