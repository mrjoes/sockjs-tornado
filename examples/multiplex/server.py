# -*- coding: utf-8 -*-

import tornado.ioloop
import tornado.web

from sockjs.tornado import SockJSConnection, SockJSRouter
from multiplex import MultiplexConnection


class IndexHandler(tornado.web.RequestHandler):
    """Regular HTTP handler to serve the chatroom page"""
    def get(self):
        self.render('index.html')


class MultiplexStaticHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('multiplex.js')


class AnnConnection(SockJSConnection):
    def on_open(self, info):
        self.send('Ann says hi!!')

    def on_message(self, message):
        self.send('Ann nods: ' + message)


class BobConnection(SockJSConnection):
    def on_open(self, info):
        self.send('Bob doesn\'t agree.')

    def on_message(self, message):
        self.send('Bob says no to: ' + message)


class CarlConnection(SockJSConnection):
    def on_open(self, info):
        self.send('Carl says goodbye!')

        self.close()


class EchoMultiplexer(MultiplexConnection):
    channels = dict(ann=AnnConnection,
                    bob=BobConnection,
                    carl=CarlConnection)

if __name__ == "__main__":
    import logging
    logging.getLogger().setLevel(logging.DEBUG)

    # Create chat router
    router = MultiplexConnection.get(ann=AnnConnection, bob=BobConnection, carl=CarlConnection)
    EchoRouter = SockJSRouter(router, '/echo')

    # Create application
    app = tornado.web.Application(
            [(r"/", IndexHandler), (r"/multiplex.js", MultiplexStaticHandler)] + EchoRouter.urls
    )
    app.listen(9999)

    tornado.ioloop.IOLoop.instance().start()
