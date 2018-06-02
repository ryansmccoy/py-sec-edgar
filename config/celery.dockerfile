FROM python:3.6.4-alpine3.7

COPY requirements/celery_app.txt /py_sec_edgar_data/requirements/celery_app.txt

RUN pip install --upgrade pip

RUN apk update \
  && apk add --virtual build-deps gcc python3-dev musl-dev \
  && apk add postgresql-dev \
  && pip install -r /py_sec_edgar_data/requirements/celery_app.txt \
  && apk del build-deps

WORKDIR /py_sec_edgar_data

COPY . /py_sec_edgar_data

CMD ["celery", "-A", "worker", "--loglevel=info"]
