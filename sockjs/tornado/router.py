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
    sockjs.tornado.router
    ~~~~~~~~~~~~~~~~~~~~~
"""

from tornado import ioloop, version_info

from sockjs.tornado import transports, session, sessioncontainer, static


DEFAULT_SETTINGS = {
    # Sessions check interval in seconds
    'session_check_interval': 1,
    # Session expiration in seconds
    'disconnect_delay': 5,
    # Heartbeat time in seconds. Do not change this value unless
    # you absolutely sure that new value will work.
    'heartbeat_delay': 25,
    # Enabled protocols
    'disabled_transports': [],
    # SockJS location
    'sockjs_url': 'http://cdn.sockjs.org/sockjs-0.1.min.js'
    }

GLOBAL_HANDLERS = [
    ('xhr_send', transports.XhrSendHandler),
    ('jsonp_send', transports.JSONPSendHandler)
]

TRANSPORTS = {
    'websocket': transports.WebSocketTransport,
    'xhr': transports.XhrPollingTransport,
    'xhr_streaming': transports.XhrStreamingTransport,
    'jsonp': transports.JSONPTransport,
    'eventsource': transports.EventSourceTransport,
    'htmlfile': transports.HtmlFileTransport
}

STATIC_HANDLERS = {
    '/chunking_test': static.ChunkingTestHandler,
    '/iframe[0-9-.a-z_]*.html': static.IFrameHandler,
    '/?': static.GreetingsHandler
}


class SockJSRouter(object):
    def __init__(self,
                 connection,
                 user_settings=dict(),
                 prefix='',
                 io_loop=None):
        # TODO: Version check
        if version_info[0] < 2:
            raise Exception('TornadIO2 requires Tornado 2.0 or higher.')

        # Store connection class
        self._connection = connection

        # Initialize io_loop
        self.io_loop = io_loop or ioloop.IOLoop.instance()

        # Settings
        self.settings = DEFAULT_SETTINGS.copy()
        if user_settings:
            self.settings.update(user_settings)

        # Sessions
        self._sessions = sessioncontainer.SessionContainer()

        check_interval = self.settings['session_check_interval']
        self._sessions_cleanup = ioloop.PeriodicCallback(self._sessions.expire,
                                                         check_interval,
                                                         self.io_loop)
        self._sessions_cleanup.start()

        # Initialize URLs
        base = prefix + r'/[^/.]+/(?P<session_id>[^/.]+)'

        # Generate global handler URLs
        self._transport_urls = [('%s/%s$' % (base, p[0]), p[1], dict(server=self))
                                for p in GLOBAL_HANDLERS]

        for k, v in TRANSPORTS.iteritems():
            if k in self.settings['disabled_transports']:
                continue

            # Only version 1 is supported
            self._transport_urls.append(
                (r'%s/%s$' % (base, k),
                 v,
                 dict(server=self))
                )

        # Generate static URLs
        map(self._transport_urls.append,
            (('%s%s' % (prefix, k), v, dict(server=self))
            for k, v in STATIC_HANDLERS.iteritems()))

    @property
    def urls(self):
        """List of the URLs to be added to the Tornado application"""
        return self._transport_urls

    def apply_routes(self, routes):
        """Feed list of the URLs to the routes list. Returns list"""
        routes.extend(self._transport_urls)
        return routes

    def create_session(self, session_id, register=True):
        """Creates new session object and returns it.

        `request`
            Request that created the session. Will be used to get query string
            parameters and cookies
        `register`
            Should be session registered in a storage. Websockets don't
            need it.
        """
        # TODO: Possible optimization here for settings.get
        s = session.Session(self._connection,
                            self,
                            session_id,
                            self.settings.get('disconnect_delay')
                            )

        if register:
            self._sessions.add(s)

        return s

    def get_session(self, session_id):
        """Get session by session id
        """
        return self._sessions.get(session_id)
