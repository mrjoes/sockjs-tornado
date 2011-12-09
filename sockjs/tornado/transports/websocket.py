# -*- coding: utf-8 -*-
#
# Copyright: (c) 2011 by the Serge S. Koval, see AUTHORS for more details.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
    sockjs.tornado.transports.websocket
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Websocket transport implementation.
"""
import logging

import tornado.escape
from tornado.websocket import WebSocketHandler

from sockjs.tornado import proto


class WebSocketTransport(WebSocketHandler):
    """Websocket tranport"""
    def initialize(self, server):
        self.server = server
        self.session = None

    # Additional verification of the websocket handshake
    # For now it will stay here, till https://github.com/facebook/tornado/pull/415
    # is merged.
    def _execute(self, transforms, *args, **kwargs):
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
        if self.request.headers.get("Connection", "").lower().find('upgrade') == -1:
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
        if not message:
            return

        try:
            msg = proto.json_decode(message)

            # TODO: Clean me up
            if isinstance(msg, list):
                for m in msg:
                    self.session.on_message(m)
            else:
                self.session.on_message(msg)
        except Exception, ex:
            print ex
            # Close session on exception
            self.close()

    def on_close(self):
        # Close session if websocket connection was closed
        if self.session is not None:
            self.session.remove_handler(self)
            self.session.close()
            self.session = None

    def send_pack(self, message):
        # Send message
        try:
            self.write_message(message)
        except IOError:
            if self.client_terminated:
                logging.debug('Dropping active websocket connection due to IOError.')

            self._detach()

    def session_closed(self):
        # If session was closed by the application, terminate websocket
        # connection as well.
        try:
            self.close()
        except Exception:
            logging.debug('Exception', exc_info=True)
        finally:
            self._detach()
