**pydexter** - a Python client for the `Dexter <http://dexter.isti.cnr.it/>`_ REST API (`documentation <http://dexterdemo.isti.cnr.it:8080/dexter-webapp/dev/#!/rest>`_)

Installation::

    python setup.py install

Usage example:

>>> import pydexter
>>> dxtr = pydexter.DexterClient("http://dexterdemo.isti.cnr.it:8080/dexter-webapp/api/")
>>> dxtr.nice_annotate("Dexter is an American television drama.", min_conf=0.8)
[u'Dexter is an ', (u'American television', u'Television_in_the_United_States'), u' drama.']

TODO: tests; some API arguments are missing.