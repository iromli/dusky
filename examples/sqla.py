import time

import tornado.web
import tornado.gen
import tornado.ioloop

import config

from dusky import MySQLConnection
from tornado.options import parse_command_line

from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.sql import select


engine = create_engine(
    'mysql://{0}:{1}@{2}/{3}'.format(
        config.DB_USER,
        config.DB_PASS,
        config.DB_HOST,
        config.DB_NAME
    )
)
metadata = MetaData(bind=engine)


Post = Table('posts', metadata, autoload=True)


def Q(sqla):
    c = sqla.compile()
    query = str(c.statement)
    args = [c.params[i] for i in c.positiontup]
    return query, args


class App(tornado.web.Application):
    @property
    def adb(self):
        return MySQLConnection(
            config.DB_HOST,
            config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASS
        )


class PostHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self):
        sqla = select([Post])
        query, args = Q(sqla)
        r = yield tornado.gen.Task(self.application.adb.query, query, *args)
        print r
        self.finish()

    @tornado.web.asynchronous
    @tornado.gen.engine
    def post(self):
        title = self.get_argument('title', None)
        content = self.get_argument('content', None)
        sqla = Post.insert().values(title=title, content=content)
        query, args = Q(sqla)
        r = yield tornado.gen.Task(self.application.adb.execute, query, *args)
        print r
        self.finish()


class PostItemHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self, post_id):
        sqla = select([Post], Post.c.id == post_id).limit(1)
        query, args = Q(sqla)
        r = yield tornado.gen.Task(self.application.adb.get, query, *args)
        print r
        self.finish()

    @tornado.web.asynchronous
    @tornado.gen.engine
    def put(self, post_id):
        title = self.get_argument('title', None)
        content = self.get_argument('content', None)
        sqla = Post.update().values(title=title, content=content)
        sqla = sqla.where(Post.c.id == post_id)
        query, args = Q(sqla)
        r = yield tornado.gen.Task(
                self.application.adb.execute_rowcount, query, *args)
        print r
        self.finish()

    @tornado.web.asynchronous
    @tornado.gen.engine
    def delete(self, post_id):
        sqla = Post.delete().where(Post.c.id == post_id)
        query, args = Q(sqla)
        r = yield tornado.gen.Task(
                self.application.adb.execute_rowcount, query, *args)
        print r
        self.finish()


class MultiPostHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def post(self):
        titles = self.get_arguments('title')
        contents = self.get_arguments('content')
        sqla = Post.insert().values(title=titles, content=contents)
        query, args = Q(sqla)
        r = yield tornado.gen.Task(
                self.application.adb.executemany_rowcount, query, args)
        print r
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
        (r"/posts", PostHandler),
        (r"/posts/(\d+)", PostItemHandler),
        (r"/posts/multi", MultiPostHandler),
    ], debug=True)
    port = 8888
    app.listen(port)

    try:
        print 'starting webserver on port %s' % port
        tornado.ioloop.IOLoop.instance().start()
    except:
        tornado.ioloop.IOLoop.instance().stop()
        raise
