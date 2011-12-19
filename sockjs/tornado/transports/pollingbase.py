# -*- coding: utf-8 -*-
"""
    sockjs.tornado.transports.pollingbase
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Polling transports base
"""

from tornado.web import asynchronous

from sockjs.tornado.basehandler import PreflightHandler


class PollingTransportBase(PreflightHandler):
    """Polling transport handler base class"""
    def initialize(self, server):
        self.server = server
        self.session = None
        self.detached = False
        self.logged = False

    def _get_session(self, session_id):
        return self.server.get_session(session_id)

    def _attach_session(self, session_id, start_heartbeat=False):
        session = self._get_session(session_id)

        if session is None:
            session = self.server.create_session(session_id)

        # Try to attach to the session
        if not session.set_handler(self, start_heartbeat):
            return False

        self.session = session

        # Verify if session is properly opened
        session.verify_state()

        return True

    def _detach(self):
        """Detach from the session"""
        if self.session:
            self.session.remove_handler(self)
            self.session = None
            self.detached = True

    @asynchronous
    def post(self, session_id):
        """Default GET handler."""
        raise NotImplementedError()

    def check_xsrf_cookie(self):
        pass

    def send_message(self, message):
        """Called by the session when some data is available"""
        raise NotImplementedError()

    def session_closed(self):
        """Called by the session when it was closed"""
        self._detach()

    # Stats
    def prepare(self):
        self.logged = True

        self.server.stats.on_conn_opened()

    def _log_disconnect(self):
        if self.logged:
            self.logged = False
            self.server.stats.on_conn_closed()

    def finish(self):
        self._log_disconnect()

        super(PollingTransportBase, self).finish()

    def on_connection_close(self):
        """Called by Tornado, when connection was closed"""
        self._log_disconnect()
        self._detach()
