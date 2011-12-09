SockJS-tornado server
=====================

SockJS-tornado is a Python server side counterpart of `SockJS-client browser library <https://github.com/sockjs/sockjs-client>`_
running on top of `Tornado <http://tornadoweb.org>`_ framework.

Simplified echo SockJS server could look more or less like::

    from tornado import web, ioloop
    from sockjs.tornado import SockJSRouter, SockJSConnection

    class EchoConnection(SockJSConnection):
        def on_message(self, msg):
            self.send(msg)

    if __name__ == '__main__':
        EchoRouter = SockJSRouter(EchoConnection, '/echo')

        app = web.Application(EchoRouter.urls)
        app.listen(9999)
        ioloop.IOLoop.instance().start()

(Take look at `examples <https://github.com/MrJoes/sockjs-tornado/tree/master/examples>`_ for a complete version).

Subscribe to `SockJS mailing list <https://groups.google.com/forum/#!forum/sockjs>`_) for discussions and support.

SockJS-tornado API
------------------

.. TBD ..
