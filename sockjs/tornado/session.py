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
    sockjs.tornado.session
    ~~~~~~~~~~~~~~~~~~~~~~

    SockJS session implementation.
"""

import logging

from sockjs.tornado import sessioncontainer, periodic, proto


class ConnectionInfo(object):
    """Connection information object.

    Will be passed to the ``on_open`` handler of your connection class.

    Has few properties:

    `ip`
        Caller IP address
    `cookies`
        Collection of cookies
    `arguments`
        Collection of the query string arguments
    """
    def __init__(self, ip, arguments, cookies):
        self.ip = ip
        self.cookies = cookies
        self.arguments = arguments

    def get_argument(self, name):
        """Return single argument by name"""
        val = self.arguments.get(name)
        if val:
            return val[0]
        return None

    def get_cookie(self, name):
        """Return single cookie by its name"""
        return self.cookies.get(name)


class Session(sessioncontainer.SessionBase):
    """SockJS session implementation.
    """

    # Session statuses
    CONNECTING = 0
    OPEN = 1
    CLOSED = 2

    def __init__(self, conn, server, session_id, expiry=None):
        """Session constructor.

        `conn`
            Default connection class
        `server`
            Associated server
        `session_id`
            Session id
        `expiry`
            Session expiry time
        """
        # Initialize session
        super(Session, self).__init__(session_id, expiry)

        self.server = server
        self.send_queue = []

        self.handler = None
        self.state = self.CONNECTING

        self.remote_ip = None

        # Create connection instance
        self.conn = conn(self)

        # Heartbeat related stuff
        self._heartbeat_timer = None
        self._heartbeat_interval = self.server.settings['heartbeat_interval'] * 1000

    # Session callbacks
    def on_delete(self, forced):
        """Session expiration callback

        `forced`
            If session item explicitly deleted, forced will be set to True. If
            item expired, will be set to False.
        """
        # Do not remove connection if it was not forced and there's running connection
        if not forced and self.handler is not None and not self.is_closed:
            self.promote()
        else:
            self.close()

    # Add session
    def set_handler(self, handler, start_heartbeat=True):
        """Set active handler for the session

        `handler`
            Associate active Tornado handler with the session
        """
        # Check if session already has associated handler
        if self.handler is not None:
            handler.send_message(proto.disconnect(2010, "Another connection still open"))
            return False

        # If IP address don't match - refuse connection
        if self.remote_ip and handler.request.remote_ip != self.remote_ip:
            logging.error('Attempted to attach to session %s (%s) from different IP (%s)' % (
                          self.session_id,
                          self.remote_ip,
                          handler.request.remote_ip
                          ))

            handler.send_message(proto.disconnect(2010, "Attempted to connect to session from different IP"))
            return False

        # Handle connection states
        if self.state == self.CONNECTING:
            self.remote_ip = handler.remote_ip

            info = ConnectionInfo(handler.remote_ip,
                      handler.request.arguments,
                      handler.request.cookies)

            # Change state
            self.state = self.OPEN

            self.send_message(proto.CONNECT)

            # Call on_open handler
            self.conn.on_open(info)
        elif self.state == self.CLOSED:
            handler.send_message(proto.disconnect(3000, "Go away!"))
            return False

        # Associate handler and promote session
        self.handler = handler
        self.promote()

        if start_heartbeat:
            self.start_heartbeat()

        return True

    def remove_handler(self, handler):
        """Remove active handler from the session

        `handler`
            Handler to remove
        """
        # Attempt to remove another handler
        if self.handler != handler:
            raise Exception('Attempted to remove invalid handler')

        self.handler = None
        self.promote()

        self.stop_heartbeat()

    def send_message(self, pack):
        """Send message

        `pack`
            Message to send
        """
        logging.debug('<<< ' + pack)

        self.send_queue.append(pack)
        self.flush()

    def flush(self):
        """Flush message queue if there's an active connection running"""
        if self.handler is None:
            return

        if not self.send_queue:
            return

        self.handler.send_message(proto.encode_messages(self.send_queue))

        self.send_queue = []

    # Close connection with all endpoints or just one endpoint
    def close(self):
        """Close session or endpoint connection.
        """
        try:
            self.conn.on_close()
        finally:
            self.state = self.CLOSED
            self.conn.is_closed = True

        # TODO: Customizable message?
        self.send_message(proto.disconnect(3000, 'Closed by the server.'))

        # Notify transport that session was closed
        if self.handler is not None:
            self.handler.session_closed()

    @property
    def is_closed(self):
        """Check if session was closed"""
        return self.state == self.CLOSED

    # Heartbeats
    def start_heartbeat(self):
        """Reset hearbeat timer"""
        self.stop_heartbeat()

        self._heartbeat_timer = periodic.Callback(self._heartbeat,
                                                  self._heartbeat_interval,
                                                  self.server.io_loop)
        self._heartbeat_timer.start()

    def stop_heartbeat(self):
        """Stop active heartbeat"""
        if self._heartbeat_timer is not None:
            self._heartbeat_timer.stop()
            self._heartbeat_timer = None

    def delay_heartbeat(self):
        """Delay active heartbeat"""
        if self._heartbeat_timer is not None:
            self._heartbeat_timer.delay()

    def _heartbeat(self):
        """Heartbeat callback"""
        self.send_message(proto.HEARTBEAT)

    # Message handler
    def on_message(self, msg):
        # TODO: Optimize me
        self.conn.on_message(msg)
