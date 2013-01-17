# -*- coding: utf-8 -*-
import itertools
import re

import tornado.ioloop
import torndb


# Borrowed from MySQLdb, used to parse the multiple insertion queries.
restr = (
    r"\svalues\s*"
    r"(\(((?<!\\)'[^\)]*?\)[^\)]*(?<!\\)?'"
    r"|[^\(\)]|"
    r"(?:\([^\)]*\))"
    r")+\))"
)
insert_values = re.compile(restr, re.IGNORECASE)


class AsyncConnection(torndb.Connection):
    """ A lightweight wrapper around async MySQLdb DB-API connection.

    The API is mostly borrowed from Torndb, except you'll need to pass
    a ``callback`` and optional ``on_error`` keyword arguments.

    Typical usage::

        adb = dusky.AsyncConnection('localhost', 'fakedb')

    The oldschool style::

        class MySQLHandler(tornado.web.RequestHandler):
            @tornado.web.asynchronous
            def get(self):
                adb.get('SELECT sleep(1)', callback=self._on_response)

            def _on_response(self, response):
                logging.info(response)
                self.finish()

    Or, use ``tornado.gen`` module::

        class MySQLHandler(tornado.web.RequestHandler):
            @tornado.web.asynchronous
            @tornado.gen.engine
            def get(self):
                response = yield tornado.gen.Task(adb.get, 'SELECT sleep(1)')
                logging.info(response)
                self.finish()
    """

    @property
    def _ioloop(self):
        return tornado.ioloop.IOLoop.instance()

    def query(self, query, *args, **kwargs):
        """Returns a row list for the given query and parameters.

        :param query: SQL query string
        :param args: A sequence of parameters
        :param kwargs: Keyword arguments, currently only
                       supports ``callback`` and ``on_error``
        """
        self._send_query(query, args)
        self._ioloop.add_handler(
            self._db.fd,
            self._collection_handler(
                callback=kwargs.pop('callback', None),
                on_error=kwargs.pop('on_error', None)
            ),
            tornado.ioloop.IOLoop.READ)

    def get(self, query, *args, **kwargs):
        """Returns the first row returned from the given query.

        :param query: SQL query string
        :param args: A sequence of parameters
        :param kwargs: Keyword arguments, currently only
                       supports ``callback`` and ``on_error``
        """
        self._send_query(query, args)
        self._ioloop.add_handler(
            self._db.fd,
            self._item_handler(
                callback=kwargs.pop('callback', None),
                on_error=kwargs.pop('on_error', None)
            ),
            tornado.ioloop.IOLoop.READ)

    def execute(self, query, *args, **kwargs):
        """Executes the given query, returning the lastrowid from the query.

        :param query: SQL query string
        :param args: A sequence of parameters
        :param kwargs: Keyword arguments, currently only
                       supports ``callback`` and ``on_error``
        """
        self.execute_lastrowid(query, *args, **kwargs)

    def execute_lastrowid(self, query, *args, **kwargs):
        """Executes the given query, returning the lastrowid from the query.

        :param query: SQL query string
        :param args: A sequence of parameters
        :param kwargs: Keyword arguments, currently only
                       supports ``callback`` and ``on_error``
        """
        self._send_query(query, args)
        self._ioloop.add_handler(
            self._db.fd,
            self._lastrow_handler(
                callback=kwargs.pop('callback', None),
                on_error=kwargs.pop('on_error', None),
            ),
            tornado.ioloop.IOLoop.READ)

    def execute_rowcount(self, query, *args, **kwargs):
        """Executes the given query, returning the rowcount from the query.

        :param query: SQL query string
        :param args: A sequence of parameters
        :param kwargs: Keyword arguments, currently only
                       supports ``callback`` and ``on_error``
        """
        self._send_query(query, args)
        self._ioloop.add_handler(
            self._db.fd,
            self._rowcount_handler(
                callback=kwargs.pop('callback', None),
                on_error=kwargs.pop('on_error', None)),
            tornado.ioloop.IOLoop.READ)

    def executemany(self, query, args, **kwargs):
        """Executes the given query against all the given param sequences.

        We return the lastrowid from the query.

        :param query: SQL query string
        :param args: A sequence of parameters
        :param kwargs: Keyword arguments, currently only
                       supports ``callback`` and ``on_error``
        """
        self.executemany_lastrowid(query, args, **kwargs)

    def executemany_lastrowid(self, query, args, **kwargs):
        """Executes the given query against all the given param sequences.

        We return the lastrowid from the query.

        :param query: SQL query string
        :param args: A sequence of parameters
        :param kwargs: Keyword arguments, currently only
                       supports ``callback`` and ``on_error``
        """
        self._send_query(query, args, is_multiple=True)
        self._ioloop.add_handler(
            self._db.fd,
            self._lastrow_handler(
                callback=kwargs.pop('callback', None),
                on_error=kwargs.pop('on_error', None)),
            tornado.ioloop.IOLoop.READ)

    def executemany_rowcount(self, query, args, **kwargs):
        """Executes the given query against all the given param sequences.

        We return the rowcount from the query.

        :param query: SQL query string
        :param args: A sequence of parameters
        :param kwargs: Keyword arguments, currently only
                       supports ``callback`` and ``on_error``
        """
        self._send_query(query, args, is_multiple=True)
        self._ioloop.add_handler(
            self._db.fd,
            self._rowcount_handler(
                callback=kwargs.pop('callback', None),
                on_error=kwargs.pop('on_error', None)),
            tornado.ioloop.IOLoop.READ)

    def close(self):
        """Remove file descriptor and close the connection.
        """
        if getattr(self, "_db", None) is not None:
            self._ioloop.remove_handler(self._db.fd)
            self._db.close()
            self._db = None

    def _send_query(self, query, args=None, is_multiple=False):
        """The actual query sent to the MySQL server.
        Each argument is escaped to prevent the security problems.
        """
        if isinstance(query, unicode):
            query = query.encode(self._db.character_set_name())
        if args is not None:
            if is_multiple:
                m = insert_values.search(query)
                if m:
                    p = m.start(1)
                    args = [m.group(1) % self._db.literal(arg) for arg in args]
                    query = ''.join([query[:p], ', '.join(args)])
            else:
                query = query % self._db.literal(args)
        self._db.send_query(query)

    def _get_rows(self, resultset):
        """The main value we provide is wrapping rows in a dict/object so that
        columns can be accessed by its key or attribute.
        """
        rows = []
        column_names = [d[0] for d in resultset.describe()]
        while True:
            r = resultset.fetch_row()
            if not r:
                break
            rows.append(r[0])
        return [torndb.Row(itertools.izip(column_names, r)) for r in rows]

    def _item_handler(self, callback=None, on_error=None):
        """Returns a row.
        """
        def inner(fd, ev):
            try:
                self._db.read_query_result()
                resultset = self._db.use_result()

                # TODO: There must be a better way to stop the iteration
                rows = self._get_rows(resultset)
                if len(rows) > 1:
                    self._throw_error(
                        Exception('Multiple rows returned for '
                                  'AsyncConnection.get() query'),
                        on_error)
                if not rows:
                    rows = None
                else:
                    rows = rows[0]
                if callback:
                    callback(rows)
            except Exception, exc:
                self._throw_error(exc, on_error)
            finally:
                self._ioloop.remove_handler(self._db.fd)
        return inner

    def _collection_handler(self, callback=None, on_error=None):
        """Returns a collection of rows.
        """
        def inner(fd, ev):
            try:
                self._db.read_query_result()
                resultset = self._db.use_result()
                rows = self._get_rows(resultset)
                if callback:
                    callback(rows)
            except Exception, exc:
                self._throw_error(exc, on_error)
            finally:
                self._ioloop.remove_handler(self._db.fd)
        return inner

    def _lastrow_handler(self, callback=None, on_error=None):
        """Return last insert ID.
        """
        def inner(fd, ev):
            try:
                self._db.read_query_result()
                resultset = self._db.insert_id()
                if callback:
                    callback(resultset)
            except Exception, exc:
                self._throw_error(exc, on_error)
            finally:
                self._ioloop.remove_handler(self._db.fd)
        return inner

    def _rowcount_handler(self, callback=None, on_error=None):
        """Returns affected rows count.
        """
        def inner(fd, ev):
            try:
                self._db.read_query_result()
                resultset = self._db.affected_rows()
                if callback:
                    callback(resultset)
            except Exception, exc:
                self._throw_error(exc, on_error)
            finally:
                self._ioloop.remove_handler(self._db.fd)
        return inner

    def _throw_error(self, exc, on_error=None):
        """Throw exception message.
        """
        if on_error:
            return on_error(exc)
        else:
            raise exc

    def iter(self, query, *args, **kwargs):
        raise NotImplementedError()

    def _cursor(self):
        raise NotImplementedError()

    def _execute(self):
        raise NotImplementedError()
