# -*- coding: utf-8 -*-
"""
    sockjs.tornado.transports.rawwebsocket
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Raw websocket transport implementation
"""
import logging
import socket

from sockjs.tornado import websocket, session, periodic, proto
from sockjs.tornado.transports import base

LOG = logging.getLogger("tornado.general")


class RawSession(session.BaseSession):
    """Raw session without any sockjs protocol encoding/decoding.
    Simply works as a proxy between `SockJSConnection` class and
    `RawWebSocketTransport`.
    """

    def __init__(self, conn, server):
        super(RawSession, self).__init__(conn, server)
        self._heartbeat_timer = None
        self._check_heartbeat_timer = None
        self._heartbeat_interval = self.server.settings['heartbeat_delay'] * 1000  # noqa
        self._heartbeat_check_delay = self.server.settings['heartbeat_check_delay']  # noqa

    def send_message(self, msg, stats=True, binary=False):
        self.handler.send_pack(msg, binary)

    def on_message(self, msg):
        self.conn.on_message(msg)

    def on_heartbeat(self):
        self.conn.on_heartbeat()

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

    def _heartbeat(self):
        if self.handler is not None:
            self.handler.ping(proto.HEARTBEAT)

            self._check_heartbeat_timer = self.server.io_loop.call_later(
                self._heartbeat_check_delay,
                self._check_heartbeat)

    def _check_heartbeat(self):
        self.stop_heartbeat()
        self.close(code=1100, message="Heartbeat timeout")


class RawWebSocketTransport(websocket.SockJSWebSocketHandler, base.BaseTransportMixin):
    """Raw Websocket transport"""
    name = 'rawwebsocket'

    def initialize(self, server):
        self.server = server
        self.session = None
        self.active = True

    def open(self):
        # Stats
        if self.server.stats:
            self.server.stats.on_conn_opened()

        # Disable nagle if needed
        if self.server.settings['disable_nagle']:
            self.stream.socket.setsockopt(
                socket.SOL_TCP, socket.TCP_NODELAY, 1)

        # Create and attach to session
        self.session = RawSession(
            self.server.get_connection_class(), self.server)
        self.session.set_handler(self)
        self.session.verify_state()
        try:
            # Verify state failed, session is closed.
            self.session.start_heartbeat()
        except:
            pass

    def on_pong(self, data):
        if hasattr(self.session, "_check_heartbeat_timer"):
            self.server.io_loop.remove_timeout(
                self.session._check_heartbeat_timer)
            self.session.on_heartbeat()

    def _detach(self):
        if self.session is not None:
            self.session.remove_handler(self)
            self.session = None

    def on_message(self, message):
        # SockJS requires that empty messages should be ignored
        if not message or not self.session:
            return

        try:
            self.session.on_message(message)
        except Exception:
            LOG.exception('RawWebSocket')

            # Close running connection
            self.abort_connection()

    def on_close(self):
        # Close session if websocket connection was closed
        if self.session is not None:
            # Stats
            if self.server.stats:
                self.server.stats.on_conn_closed()

            session = self.session
            self._detach()
            session.close()

    def send_pack(self, message, binary=False):
        # Send message
        try:
            self.write_message(message, binary)
        except IOError:
            self.server.io_loop.add_callback(self.on_close)

    def session_closed(self):
        try:
            self.close()
        except IOError:
            pass
        finally:
            self._detach()

    # Websocket overrides
    def allow_draft76(self):
        return True
