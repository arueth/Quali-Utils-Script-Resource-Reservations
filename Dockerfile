FROM alpine:3.5

WORKDIR /usr/src/script

COPY resource_availability/ ./resource_availability/

RUN apk update \
&& apk upgrade \
&& apk add python py-pip \
&& rm -rf /var/cache/apk/* \
&& pip install -U pip \
&& pip install -r /usr/src/script/resource_availability/requirements.txt \
&& ln -s /usr/src/script/resource_availability/availability_cron.py /etc/periodic/hourly/availability_cron

ENV CROND_LOG_LEVEL=6

CMD crond -f -d $CROND_LOG_LEVEL