#!/bin/sh

pip install supervisor

echo "Wait rabbitMQ to start.."
sleep 10;

echo "Starting Celery through supervisord"
/usr/local/bin/supervisord -c scripts/docker/supervisord.conf

echo "Logging.."
/usr/local/bin/supervisorctl tail -f celeryd
