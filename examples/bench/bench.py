# -*- coding: utf-8 -*-
import sys

from tornado import web, ioloop

from sockjs.tornado import SockJSRouter, SockJSConnection


class EchoConnection(SockJSConnection):
    clients = set()

    def on_open(self, info):
        self.clients.add(self)

    def on_message(self, msg):
        self.broadcast(self.clients, msg)

    def on_close(self):
        self.clients.remove(self)

    @classmethod
    def dump_stats(self):
        print 'Clients: %d' % (len(self.clients))

if __name__ == '__main__':
    options = dict()

    if len(sys.argv) > 1:
        options['immediate_flush'] = False

    EchoRouter = SockJSRouter(EchoConnection, '/echo', options)

    app = web.Application(EchoRouter.urls)

    app.listen(8080)

    ioloop.PeriodicCallback(EchoConnection.dump_stats, 1000).start()

    ioloop.IOLoop.instance().start()
