=====================
Python SEC Edgar Data
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


Install
-------

.. code-block:: bash

    $  docker run -d -p 5672:5672 -p 15672:15672 --name sec-rabbit rabbitmq:management
    $  celery -A edgar_download.celery_download_complete_submission_filing worker --loglevel=info
    $  python -A edgar_download.celery_download_complete_submission_filing worker --loglevel=info


or the latest development version from github:

.. code-block:: bash

    $ pip install git+https://github.com/hootnot/oanda-api-v20.git

If you want to run the tests, clone the repository:

.. code-block:: bash

    $ git clone https://github.com/hootnot/oanda-api-v20
    $ cd oanda-api-v20

    # install necessary packages for testing
    $ grep "\- pip install" .travis.yml |
    > while read LNE
    > do `echo $LNE| cut -c2-` ; done

    $ python setup.py test
    $ python setup.py install

Examples are provided in the https://github.com/hootnot/oandapyV20-examples
repository.
