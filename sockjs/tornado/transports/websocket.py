# -*- coding: utf-8 -*-
"""
    sockjs.tornado.transports.websocket
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Websocket transport implementation
"""
import logging

from sockjs.tornado import proto, websocket


class WebSocketTransport(websocket.WebSocketHandler):
    """Websocket transport"""
    def initialize(self, server):
        self.server = server
        self.session = None

    def open(self, session_id):
        self.session = self.server.create_session(session_id, register=False)

        if not self.session.set_handler(self):
            self.close()
            return

        self.session.verify_state()

        if self.session:
            self.session.flush()

    def _detach(self):
        if self.session is not None:
            self.session.remove_handler(self)
            self.session = None

    def on_message(self, message):
        # Ignore empty messages
        if not message or not self.session:
            return

        try:
            msg = proto.json_decode(message)

            # TODO: Clean me up
            if isinstance(msg, list):
                for m in msg:
                    self.session.on_message(m)
            else:
                self.session.on_message(msg)
        except Exception:
            logging.exception('WebSocket incoming')
            # Close session on exception
            self.close()

    def on_close(self):
        # Close session if websocket connection was closed
        if self.session is not None:
            self.session.remove_handler(self)

            try:
                # Can blow up if socket is already closed
                self.session.close()
            except IOError:
                pass

            self.session = None

    def send_pack(self, message):
        # Send message
        try:
            self.write_message(message)
        except IOError:
            if self.client_terminated:
                logging.debug('Dropping active websocket connection due to IOError.')

            # Close on next tick to prevent calling connections on_close
            # as a result of send() message call
            self.server.io_loop.add_callback(self.on_close)

    def session_closed(self):
        # If session was closed by the application, terminate websocket
        # connection as well.
        try:
            self.close()
        except Exception:
            logging.debug('Exception', exc_info=True)
        finally:
            self._detach()
