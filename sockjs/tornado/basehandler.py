# -*- coding: utf-8 -*-
"""
    sockjs.tornado.basehandler
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Various base http handlers
"""

import datetime
import socket
import logging

from tornado.web import asynchronous, RequestHandler

CACHE_TIME = 31536000


class BaseHandler(RequestHandler):
    def initialize(self, server):
        self.server = server
        self.logged = False

    # Statistics
    def prepare(self):
        self.logged = True
        self.server.stats.on_conn_opened()

    def _log_disconnect(self):
        if self.logged:
            self.server.stats.on_conn_closed()
            self.logged = False

    def finish(self):
        self._log_disconnect()

        super(BaseHandler, self).finish()

    def on_connection_close(self):
        self._log_disconnect()

    # Various helpers
    def enable_cache(self):
        self.set_header('Cache-Control', 'max-age=%d, public' % CACHE_TIME)

        d = datetime.datetime.now() + datetime.timedelta(seconds=CACHE_TIME)
        self.set_header('Expires', d.strftime('%a, %d %b %Y %H:%M:%S'))

        self.set_header('access-control-max-age', CACHE_TIME)

    def disable_cache(self):
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')

    def handle_session_cookie(self):
        cookie = self.cookies.get('JSESSIONID')

        if not cookie:
            cv = 'dummy'
        else:
            cv = cookie.value

        self.set_cookie('JSESSIONID', cv)

    def safe_finish(self):
        try:
            self.finish()
        except (socket.error, IOError):
            # We don't want to raise IOError exception if finish() call fails.
            # It can happen if connection is set to Keep-Alive, but client
            # closes connection after receiving response.
            logging.debug('Ignoring IOError in safe_finish()')
            pass


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
