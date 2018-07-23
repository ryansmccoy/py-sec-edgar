from __future__ import absolute_import

from celery import Celery

celery = Celery('tasks', broker="amqp://sec:data@127.0.0.1:5672/sec")

celery.conf.update(CELERY_ACCEPT_CONTENT=['json', 'application/x-python-serialize'],
                   CELERY_TASK_SERIALIZER='json',
                   CELERY_RESULT_SERIALIZER='json')
