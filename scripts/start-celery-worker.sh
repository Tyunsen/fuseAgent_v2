#!/bin/bash

set -o errexit
set -o nounset

export LOCAL_QUEUE_NAME=${NODE_IP}
if [ -z "${LOCAL_QUEUE_NAME}" ]; then
    export LOCAL_QUEUE_NAME="localhost"
fi

export CELERY_WORKER_CONCURRENCY=${CELERY_WORKER_CONCURRENCY:-4}
export CELERY_WORKER_POOL=${CELERY_WORKER_POOL:-threads}

exec celery -A config.celery worker -l INFO --concurrency=${CELERY_WORKER_CONCURRENCY} -Q ${LOCAL_QUEUE_NAME},celery --pool=${CELERY_WORKER_POOL}
