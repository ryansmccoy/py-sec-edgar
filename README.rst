=====================
Python SEC Edgar Data (Currently Under Developement)
=====================

.. image:: https://img.shields.io/pypi/v/py_sec_edgar_data.svg
        :target: https://pypi.python.org/pypi/py_sec_edgar_data

.. image:: https://img.shields.io/travis/ryan413/py_sec_edgar_data.svg
        :target: https://travis-ci.org/ryan413/py_sec_edgar_data

.. image:: https://readthedocs.org/projects/py-sec-edgar-data/badge/?version=latest
        :target: https://py-sec-edgar-data.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


Python package used to download SEC Edgar filings

.. image:: https://raw.githubusercontent.com/ryan413/py-sec-edgar-data/master/docs/folder_structure.png

* Documentation: https://py-sec-edgar-data.readthedocs.io.

Run
-------

.. code-block:: Bash (Work in Progress)

    $  docker run -d -p 5672:5672 -p 15672:15672 --name sec-rabbit rabbitmq:management
    $  celery -A edgar_download.celery_download_complete_submission_filing worker --loglevel=info


.. code-block:: Docker (Work in Progress)

