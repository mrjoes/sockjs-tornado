import logging

from tornado.web import asynchronous

from sockjs.tornado.basehandler import BaseHandler


class PreflightHandler(BaseHandler):
    """CORS preflight handler"""

    @asynchronous
    def options(self, *args, **kwargs):
        """XHR cross-domain OPTIONS handler"""
        self.enable_cache()
        self.handle_session_cookie()
        self.preflight()

        if self.verify_origin():
            self.set_status(204)

            self.set_header('Access-Control-Allow-Methods', 'OPTIONS, POST')
            self.set_header('Allow', 'OPTIONS, POST')
        else:
            # Set forbidden
            self.set_status(403)

        self.finish()

    def preflight(self):
        """Handles request authentication"""
        origin = self.request.headers.get('Origin', '*')

        self.set_header('Access-Control-Allow-Origin', origin)

        headers = self.request.headers.get('Access-Control-Allow-Headers')
        if headers:
            self.set_header('Access-Control-Allow-Header', headers)

        self.set_header('Access-Control-Allow-Credentials', 'true')

    def verify_origin(self):
        """Verify if request can be served"""
        # TODO: Verify origin
        return True


class PollingTransportBase(PreflightHandler):
    """Polling handler base"""
    def initialize(self, server):
        self.server = server
        self.session = None

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

    def on_connection_close(self):
        """Called by Tornado, when connection was closed"""
        self._detach()
