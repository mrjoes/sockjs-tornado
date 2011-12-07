from tornado.web import asynchronous

from sockjs.tornado.transports import pollingbase


class XhrStreamingTransport(pollingbase.PollingTransportBase):
    name = 'xhr-streaming'

    @asynchronous
    def post(self, session_id):
        # Handle cookie
        self.preflight()
        self.handle_session_cookie()
        self.set_header('Content-Type', 'application/javascript; charset=UTF-8')

        # Send prelude and flush any pending messages
        self.send_pack('h' * 2048)

        if not self._attach_session(session_id, False):
            self.finish()
            return

        if self.session is not None:
            self.session.flush()

    def send_pack(self, message):
        self.write(message + '\n')
        self.flush()

        # TODO: Close connection based on amount of data transferred
