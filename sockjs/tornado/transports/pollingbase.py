import logging

from tornado import asynchronous
from tornado.web import RequestHandler

from sockjs.tornado import proto


class PreflightHandler(RequestHandler):
    """CORS preflight handler"""

    @asynchronous
    def options(self, *args, **kwargs):
        """XHR cross-domain OPTIONS handler"""
        self.preflight()
        self.finish()

    def preflight(self):
        """Handles request authentication"""
        if 'Origin' in self.request.headers:
            if self.verify_origin():
                self.set_header('Access-Control-Allow-Origin',
                                self.request.headers['Origin'])

                if 'Cookie' in self.request.headers:
                    self.set_header('Access-Control-Allow-Credentials', True)

                self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

                return True
            else:
                return False
        else:
            return True

    def verify_origin(self):
        """Verify if request can be served"""
        # TODO: Verify origin
        return True


class PollingTransportBase(PreflightHandler):
    """Polling handler base"""
    def initialize(self, server):
        self.server = server
        self.session = None

        logging.debug('Initializing %s transport.' % self.name)

    def _get_session(self, session_id):
        return self.server.get_session(session_id)

    def _get_or_create_session(self, session_id):
        session = self._get_session(session_id)

        if session is None:
            session = self.server.create_session(session_id)

        return session

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

