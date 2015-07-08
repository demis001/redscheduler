Tests
=====

Install test requirements via included requirements.txt here

.. code-block:: bash

    pip install -r requirements.txt

If you are running python 2.6 then you have to also ensure you install unittest2

.. code-block:: bash

    pip install unittest2

Tests are run using nosetests or you can use tox to run tests inside of virtualenvs
automatically using many different python versions
the tox.ini file in the top level directory will automatically install all dependencies
for you for each version of python

.. code-block:: bash

    tox
