#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

docker container run \
        -d \
        --name quali_utils_cron \
        -e CLOUDSHELL_DOMAIN=Global \
        -e CLOUDSHELL_SERVER=localhost \
        -v ${DIR}/../dev-secrets/cloudshell_password.txt:/run/secrets/cloudshell_password \
        -v ${DIR}/../dev-secrets/cloudshell_user.txt:/run/secrets/cloudshell_user \
        -v quali_utils_cron_configs:/usr/src/script/config \
        -v quali_utils_data:/usr/src/script/data \
        arueth/quali-utils-cron:latest
