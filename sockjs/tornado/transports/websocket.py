# -*- coding: utf-8 -*-
"""
    sockjs.tornado.transports.websocket
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Websocket transport implementation
"""
import logging

import tornado.escape
from tornado import stack_context
from tornado.websocket import WebSocketHandler

from sockjs.tornado import proto


class WebSocketTransport(WebSocketHandler):
    """Websocket transport"""
    def initialize(self, server):
        self.server = server
        self.session = None

    # Additional verification of the websocket handshake
    # For now it will stay here, till https://github.com/facebook/tornado/pull/415
    # is merged.
    def _execute(self, transforms, *args, **kwargs):
        with stack_context.ExceptionStackContext(self._handle_websocket_exception):
            # Websocket only supports GET method
            if self.request.method != 'GET':
                self.stream.write(tornado.escape.utf8(
                    "HTTP/1.1 405 Method Not Allowed\r\n\r\n"
                ))
                self.stream.close()
                return

            # Upgrade header should be present and should be equal to WebSocket
            if self.request.headers.get("Upgrade", "").lower() != 'websocket':
                self.stream.write(tornado.escape.utf8(
                    "HTTP/1.1 400 Bad Request\r\n\r\n"
                    "Can \"Upgrade\" only to \"WebSocket\"."
                ))
                self.stream.close()
                return

            # Connection header should be upgrade. Some proxy servers/load balancers
            # might mess with it.
            headers = self.request.headers
            connection = map(lambda s: s.strip().lower(), headers.get("Connection", "").split(","))
            if 'upgrade' not in connection:
                self.stream.write(tornado.escape.utf8(
                    "HTTP/1.1 400 Bad Request\r\n\r\n"
                    "\"Connection\" must be \"Upgrade\"."
                ))
                self.stream.close()
                return

            super(WebSocketTransport, self)._execute(transforms, *args, **kwargs)

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

    def _handle_websocket_exception(self, type, value, traceback):
        if type is IOError:
            self.server.io_loop.add_callback(self.on_connection_close)

            # raise (type, value, traceback)
            logging.debug('Exception', exc_info=(type, value, traceback))
            return True
