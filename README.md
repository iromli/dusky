Dusky
=====

Dusky is a small MySQL wrapper on top of async MySQLdb, patched for use in Tornado-based app.

Install
-------

Since Dusky is not available at [pypi](http://pypi.python.org), you'll need to
grab this library manually:

* `python setup.py install`
* use `pip install -r requirements.txt` to install async MySQLdb.

Example
-------

Let's create `app.py` to run a simple example.

```python
import time

import tornado.web
import tornado.gen
import tornado.ioloop

from dusky import AsyncConnection
from tornado.options import parse_command_line


class App(tornado.web.Application):
    @property
    def adb(self):
        return AsyncConnection(
            'localhost', 'fakedb', user='root', password='s3cr3t')


class MySQLHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self):
        yield tornado.gen.Task(self.application.adb.get, 'SELECT sleep(1)')
        self.finish()


class TimedOutHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self):
        yield tornado.gen.Task(
            tornado.ioloop.IOLoop.instance().add_timeout, time.time() + 1)
        self.finish()


if __name__ == '__main__':
    parse_command_line()
    app = App([
        (r"/", TimedOutHandler),
        (r"/mysql", MySQLHandler)
    ], debug=True)
    app.listen(8888)

    try:
        tornado.ioloop.IOLoop.instance().start()
    except:
        tornado.ioloop.IOLoop.instance().stop()
        raise
```

Afterwards, run the `python app.py`, open new console window, use `siege` or `ab` tool to start load testing:

    ab -c 100 -n 10000 localhost:8888/

Open new console window (again):

    ab -c 100 -n 10000 localhost:8888/mysql

You'll see that those two URLs running in concurrent.

Kudos
-----

* [The original idea](http://is.gd/e5Lt4d)
* [A fork of MySQLdb](https://github.com/eliast/async-MySQL-python)
* [Torndb](https://github.com/bdarnell/torndb), the blocking MySQL wrapper, for its API
