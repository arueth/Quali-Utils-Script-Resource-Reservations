FROM alpine:3.5

RUN apk update \
&& apk upgrade \
&& apk add python py-pip \
&& rm -rf /var/cache/apk/* \
&& pip install -U pip

WORKDIR /usr/src/script

COPY resource_availability/requirements.txt ./resource_availability/

RUN pip install -r /usr/src/script/resource_availability/requirements.txt

COPY resource_availability/ ./resource_availability/

RUN ln -s /usr/src/script/resource_availability/availability_cron.py /etc/periodic/hourly/availability_cron

ENV CROND_LOG_LEVEL=6

CMD run-parts /etc/periodic/hourly && crond -f -d $CROND_LOG_LEVEL
