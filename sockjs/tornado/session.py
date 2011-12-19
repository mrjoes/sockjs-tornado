# -*- coding: utf-8 -*-
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


# Session states
CONNECTING = 0
OPEN = 1
CLOSED = 2


class Session(sessioncontainer.SessionBase):
    """SockJS session implementation.
    """

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
        self.stats = server.stats
        self.send_queue = ''

        self.handler = None
        self.state = CONNECTING

        self.remote_ip = None

        # Create connection instance
        self.conn = conn(self)

        # Heartbeat related stuff
        self._heartbeat_timer = None
        self._heartbeat_interval = self.server.settings['heartbeat_delay'] * 1000

        self._immediate_flush = self.server.settings['immediate_flush']
        self._pending_flush = False

        # Bump stats
        self.stats.sess_active += 1

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
            handler.send_pack(proto.disconnect(2010, "Another connection still open"))
            return False

        if self.state == OPEN:
            # If IP address doesn't match - refuse connection
            if handler.request.remote_ip != self.remote_ip:
                logging.error('Attempted to attach to session %s (%s) from different IP (%s)' % (
                              self.session_id,
                              self.remote_ip,
                              self.handler.request.remote_ip
                              ))

                handler.send_pack(proto.disconnect(2010, "Attempted to connect to session from different IP"))
                return False
        elif self.state == CLOSED:
            handler.send_pack(proto.disconnect(3000, "Go away!"))
            return False

        # Associate handler and promote session
        self.handler = handler
        self.promote()

        if start_heartbeat:
            self.start_heartbeat()

        return True

    def verify_state(self):
        # Verify connection state
        if self.state == CONNECTING:
            self.remote_ip = self.handler.request.remote_ip

            info = ConnectionInfo(self.handler.request.remote_ip,
                      self.handler.request.arguments,
                      self.handler.request.cookies)

            # Change state
            self.state = OPEN

            # Send CONNECT message
            self.handler.send_pack(proto.CONNECT)

            # Call on_open handler
            self.conn.on_open(info)

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

    def send_message(self, msg):
        """Send message

        `msg`
            JSON encoded string to send
        """
        assert isinstance(msg, basestring), 'Can only send strings'

        if isinstance(msg, unicode):
            msg = msg.encode('utf-8')

        self.stats.on_pack_sent(1)

        if self._immediate_flush:
            if self.handler and not self.send_queue:
                # Send message right away
                self.handler.send_pack('a[%s]' % msg)
            else:
                if self.send_queue:
                    self.send_queue += ','
                self.send_queue += msg

                self.flush()
        else:
            if self.send_queue:
                self.send_queue += ','
            self.send_queue += msg

            if not self._pending_flush:
                self.server.io_loop.add_callback(self.flush)
                self._pending_flush = True

    def flush(self):
        """Flush message queue if there's an active connection running"""
        self._pending_flush = False

        if self.handler is None:
            return

        if not self.send_queue:
            return

        self.handler.send_pack('a[%s]' % self.send_queue)
        self.send_queue = ''

    # Close connection with all endpoints or just one endpoint
    def close(self):
        """Close session or endpoint connection.
        """
        if not self.is_closed:
            try:
                self.conn.on_close()
            except:
                logging.debug("Failed to call on_close().", exc_info=True)
            finally:
                self.state = CLOSED

                # Bump stats
                self.stats.sess_active -= 1

        if self.handler is not None:
            self.handler.send_pack(proto.disconnect(3000, 'Go away!'))
            self.handler.session_closed()

    def delayed_close(self):
        self.server.io_loop.add_callback(self.close)

    @property
    def is_closed(self):
        """Check if session was closed"""
        return self.state == CLOSED

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
        if self.handler is not None:
            self.handler.send_pack(proto.HEARTBEAT)
        else:
            self.stop_heartbeat()

    # Message handler
    def on_messages(self, msg_list):
        self.stats.on_pack_recv(len(msg_list))

        for msg in msg_list:
            self.conn.on_message(msg)
