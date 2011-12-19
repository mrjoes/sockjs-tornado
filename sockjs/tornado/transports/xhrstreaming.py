# -*- coding: utf-8 -*-
"""
    sockjs.tornado.transports.xhrstreaming
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Xhr-Streaming transport implementation
"""

from tornado.web import asynchronous

from sockjs.tornado.transports import pollingbase


class XhrStreamingTransport(pollingbase.PollingTransportBase):
    name = 'xhr-streaming'

    @asynchronous
    def post(self, session_id):
        # Handle cookie
        self.preflight()
        self.handle_session_cookie()
        self.set_header('Content-Type', 'application/javascript; charset=UTF-8')

        # Send prelude and flush any pending messages
        self.send_pack('h' * 2048)

        if not self._attach_session(session_id, False):
            self.finish()
            return

        if self.session:
            self.session.flush()

    def send_pack(self, message):
        try:
            self.write(message + '\n')
            self.flush()
        except IOError:
            # If connection dropped, make sure we close offending session instead
            # of propagating error all way up.
            self.session.delayed_close()
            self._detach()

        # TODO: Close connection based on amount of data transferred
