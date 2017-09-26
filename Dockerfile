FROM ubuntu:xenial

MAINTAINER Reinout van Rees <reinout.vanrees@nelen-schuurmans.nl>

# Change the date to force rebuilding the whole image
ENV REFRESHED_AT 1972-12-25

# system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python-dev \
    python-gdal \
    python-lxml \
    python-pip \
&& apt-get clean -y && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools
RUN pip install zc.buildout

VOLUME /code
WORKDIR /code
