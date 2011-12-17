# -*- coding: utf-8 -*-
import math

from tornado import web, ioloop

from sockjs.tornado import SockJSRouter, SockJSConnection


class EchoConnection(SockJSConnection):
    def on_message(self, msg):
        self.send(msg)


class CloseConnection(SockJSConnection):
    def on_open(self, info):
        self.close()

    def on_message(self, msg):
        pass


class TickerConnection(SockJSConnection):
    def on_open(self, info):
        self.timeout = ioloop.PeriodicCallback(self._ticker, 1000)
        self.timeout.start()

    def on_close(self):
        self.timeout.stop()

    def _ticker(self):
        self.send('tick!')


class BroadcastConnection(SockJSConnection):
    clients = set()

    def on_open(self, info):
        self.clients.add(self)

    def on_message(self, msg):
        self.broadcast(self.clients, msg)

    def on_close(self):
        self.clients.remove(self)


class AmplifyConnection(SockJSConnection):
    def on_message(self, msg):
        n = math.floor(float(msg))
        if n < 0 or n > 19:
            n = 1

        self.send('x' * (math.pow(2, n) + 1))

if __name__ == '__main__':
    import logging
    logging.getLogger().setLevel(logging.DEBUG)

    EchoRouter = SockJSRouter(EchoConnection, '/echo')
    WSOffRouter = SockJSRouter(EchoConnection, '/disabled_websocket_echo',
                            user_settings=dict(disabled_transports=['websocket']))
    CloseRouter = SockJSRouter(CloseConnection, '/close')
    TickerRouter = SockJSRouter(TickerConnection, '/ticker')
    AmplifyRouter = SockJSRouter(AmplifyConnection, '/amplify')
    BroadcastRouter = SockJSRouter(BroadcastConnection, '/broadcast')

    app = web.Application(EchoRouter.urls +
                          WSOffRouter.urls +
                          CloseRouter.urls +
                          TickerRouter.urls +
                          AmplifyRouter.urls +
                          BroadcastRouter.urls
                          )

    app.listen(8080)
    ioloop.IOLoop.instance().start()
