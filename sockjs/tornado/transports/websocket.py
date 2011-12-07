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

from tornado.websocket import WebSocketHandler

from sockjs.tornado import proto


class WebSocketTransport(WebSocketHandler):
    """Websocket tranport"""
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
        if not message:
            return

        print '>>>', message

        try:
            msg = proto.json_load(message)

            print 'DUMP', msg

            # TODO: Verify
            if isinstance(msg, list):
                for m in msg:
                    self.session.on_message(m)
            else:
                self.session.on_message(msg)
        except Exception:
            # Close session on exception
            self.close()

    def on_close(self):
        # Close session if websocket connection was closed
        if self.session is not None:
            self.session.remove_handler(self)
            self.session.close()
            self.session = None

            print 'Closed'

    def send_pack(self, message):
        # Send message
        try:
            print '<<<', message
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
