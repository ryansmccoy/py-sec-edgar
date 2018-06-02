FROM continuumio/miniconda3

RUN apt-get update && apt-get install -y \
 libpq-dev \
 build-essential \
 rabbitmq-server \
&& rm -rf /var/lib/apt/lists/*

RUN mkdir /config
RUN mkdir /data
RUN mkdir /py_sec_edgar_data
RUN mkdir /sec_gov

RUN conda install pandas numpy sqlalchemy psycopg2 cython scipy cryptography pyodbc lxml

COPY config/rabbitmq.config /etc/rabbitmq/rabbitmq.config
COPY config/definitions.json /etc/rabbitmq/definitions.json

ADD requirements/requirements.txt /py_sec_edgar_data/requirements.txt

ADD ./py_sec_edgar_data/ /py_sec_edgar_data/
ADD ./config/ /config/
ADD ./data/ /data/

RUN pip install -r /py_sec_edgar_data/requirements.txt
#
EXPOSE 15672

CMD ["rabbitmq-plugins","enable","sec","data"]
CMD ["rabbitmqctl","add_user","sec","data"]
CMD ["rabbitmqctl","add_vhost","sec"]

# CMD ["/opt/conda/bin/celery", "-A", "py_sec_edgar_data.tasks", "worker", "--loglevel=info"]
ENTRYPOINT celery -A py_sec_edgar_data.tasks worker --loglevel=info
