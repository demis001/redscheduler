Installation
============

Virtualenv
----------

Most likely you will want to install into a virtualenv to keep your code separate
from the system's python packages.

This portion is completely optional

.. code-block:: bash

    python setup.py bootstrap_virtualenv venv --prompt="(redscheduler)"
    source venv/bin/activate

Install redscheduler
--------------------

.. code-block:: bash

    pip install -r requirements.txt
    python setup.py install

For python 2.6 you will need to also install ordereddict

.. code-block:: bash

    pip install ordereddict
