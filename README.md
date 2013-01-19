Dusky
=====

Dusky is a lightweight wrapper around async MySQLdb, that works within Tornado IOLoop. Note, this library is not tested in production yet. Use Dusky at your own risk.

Install
-------

Since Dusky is not available at [PyPI](http://pypi.python.org), you'll need to
grab this library manually:

* `python setup.py install`
* use `pip install -e git://github.com/eliast/async-MySQL-python.git@master#egg=mysqldb-dev` to install the async MySQLdb

Kudos
-----

* [The original idea](http://is.gd/e5Lt4d)
* [A fork of MySQLdb](https://github.com/eliast/async-MySQL-python)
* [Torndb](https://github.com/bdarnell/torndb), the blocking MySQL wrapper, for its API

Copyright
---------

Dusky is released under MIT license. See `LICENSE.txt` for details.
