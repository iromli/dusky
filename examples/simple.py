import time

import tornado.web
import tornado.gen
import tornado.ioloop

import config

from dusky import AsyncConnection
from tornado.options import parse_command_line


class App(tornado.web.Application):
    @property
    def adb(self):
        return AsyncConnection(
            config.DB_HOST,
            config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASS
        )


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
