# -*- coding: utf-8 -*-
"""
    sockjs.tornado.conn
    ~~~~~~~~~~~~~~~~~~~

    SockJS connection interface
"""
from sockjs.tornado import proto


class SockJSConnection(object):
    def __init__(self, session):
        """Connection constructor.

        `session`
            Associated session
        """
        self.session = session

    # Public API
    def on_open(self, request):
        """Default on_open() handler.

        Override when you need to do some initialization or request validation.
        If you return False, connection will be rejected.

        You can also throw Tornado HTTPError to close connection.

        `request`
            ``ConnectionInfo`` object which contains caller IP address, query string
            parameters and cookies associated with this request.

        For example::

            class MyConnection(SocketConnection):
                def on_open(self, request):
                    self.user_id = request.get_argument('id', None)

                    if not self.user_id:
                        return False

        """
        pass

    def on_message(self, message):
        """Default on_message handler. Must be overridden in your application"""
        raise NotImplementedError()

    def on_close(self):
        """Default on_close handler."""
        pass

    def send(self, message):
        """Send message to the client.

        `message`
            Message to send.
        """
        if not self.is_closed:
            self.session.stats.on_pack_sent(1)

            self.session.send_message(proto.json_encode(message))

    def broadcast(self, clients, message):
        msg = proto.json_encode(message)

        # We don't want to use len() because clients might be iterator and
        # not a list.
        count = 0

        for c in clients:
            if not c.is_closed:
                c.session.send_message(msg)
                count += 1

        self.session.stats.on_pack_sent(count)

    def close(self):
        self.session.close()

    @property
    def is_closed(self):
        """Check if session was closed"""
        return self.session.is_closed
