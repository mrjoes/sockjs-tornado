# -*- coding: utf-8 -*-

import tornado.ioloop
import tornado.web

import sockjs.tornado


class IndexHandler(tornado.web.RequestHandler):
    """Regular HTTP handler to serve the chatroom page"""
    def get(self):
        self.render('index.html')


class ChatConnection(sockjs.tornado.SockJSConnection):
    # Class level variable
    participants = set()

    def broadcast(self, msg):
        for p in self.participants:
            p.send(msg)

    def on_open(self, info):
        self.broadcast("Someone joined.")

        self.participants.add(self)

    def on_message(self, message):
        self.broadcast(message)

    def on_close(self):
        self.participants.remove(self)

        self.broadcast("Someone left.")

if __name__ == "__main__":
    import logging
    logging.getLogger().setLevel(logging.DEBUG)

    # Create chat router
    ChatRouter = sockjs.tornado.SockJSRouter(ChatConnection, '/chat')

    # Create application
    app = tornado.web.Application(
            [(r"/", IndexHandler)] + ChatRouter.urls
    )
    app.listen(8080)

    tornado.ioloop.IOLoop.instance().start()
