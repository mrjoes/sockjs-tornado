# -*- coding: utf-8 -*-

import tornado.ioloop
import tornado.web

from sockjs.tornado import SockJSConnection, SockJSRouter, proto


class IndexHandler(tornado.web.RequestHandler):
    """Regular HTTP handler to serve the ping page"""
    def get(self):
        self.render('index.html')


class StatsHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('stats.html')


# Out broadcast connection
class BroadcastConnection(SockJSConnection):
    clients = set()

    def on_open(self, info):
        self.clients.add(self)

    def on_message(self, msg):
        self.broadcast(self.clients, msg)

    def on_close(self):
        self.clients.remove(self)

BroadcastRouter = SockJSRouter(BroadcastConnection, '/broadcast')


# Stats class
class StatsConnection(SockJSConnection):
    def on_open(self, info):
        self.loop = tornado.ioloop.PeriodicCallback(self._send_stats, 1000)
        self.loop.start()

    def on_message(self):
        pass

    def on_close(self):
        self.loop.stop()

    def _send_stats(self):
        data = proto.json_encode(BroadcastRouter.stats.dump())
        self.send(data)

StatsRouter = SockJSRouter(StatsConnection, '/statsconn')

if __name__ == "__main__":
    import logging
    logging.getLogger().setLevel(logging.DEBUG)

    # Create application
    app = tornado.web.Application(
            [(r"/", IndexHandler), (r"/stats", StatsHandler)] +
            BroadcastRouter.urls +
            StatsRouter.urls
    )
    app.listen(8080)

    print 'Listening on 0.0.0.0:8080'

    tornado.ioloop.IOLoop.instance().start()
