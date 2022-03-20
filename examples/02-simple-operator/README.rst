=======================
Simple Operator Example
=======================

This example includes a simple operator that is built using `Kopf
<https://kopf.readthedocs.io>`_. Kopf makes the bootstrapping of the operator
very easy.


Running example
---------------

In order to run this example, you can use ``poetry`` in this project::

  $ cd examples/02-simple-operator/
  $ poetry run kopf run watcher.py --verbose

Note that if you aren't using ``poetry``, you can also run this simply by
installing all dependencies in a virtualenv and running::

  $ kopf run watcher.py --verbose

