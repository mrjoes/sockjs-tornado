# -*- coding: utf-8 -*-

from tornado import web, httpserver, ioloop

from sockjs.tornado import SockJSRouter, SockJSConnection


class EchoConnection(SockJSConnection):
    def on_message(self, msg):
        self.send(msg)


class CloseConnection(SockJSConnection):
    def on_open(self, info):
        self.close()

    def on_message(self, msg):
        pass


if __name__ == '__main__':
    import logging
    logging.getLogger().setLevel(logging.DEBUG)

    EchoRouter = SockJSRouter(EchoConnection, '/echo')

    CloseRouter = SockJSRouter(CloseConnection, '/close')

    WSOffRouter = SockJSRouter(EchoConnection, '/disabled_websocket_echo',
                            user_settings=dict(disabled_transports=['websocket']))

    http_app = web.Application(EchoRouter.urls +
                               CloseRouter.urls +
                               WSOffRouter.urls)

    http_server = httpserver.HTTPServer(http_app)
    http_server.listen(8080)

    ioloop.IOLoop.instance().start()
