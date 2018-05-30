#!/usr/bin/env bash

source activate secdata

cd /home/ryan/SECDATA/sec-data-python/sec_data/

celery -A py_sec_edgar_data.celery_consumer_filings worker --loglevel=info --concurrency=1
