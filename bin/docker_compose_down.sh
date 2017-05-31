#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

docker-compose -p qualiutilsdc -f ${DIR}/../docker-compose.yml -f ${DIR}/../docker-compose.override.yml down
