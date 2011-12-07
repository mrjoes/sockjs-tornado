from tornado.web import asynchronous

from sockjs.tornado.transports import pollingbase


class XhrStreamingTransport(pollingbase.PollingTransportBase):
    name = 'xhr-streaming'

    @asynchronous
    def post(self, session_id):
        self.session = self._get_or_create_session(session_id)

        if not self.session.set_handler(self):
            self.finish()
            return

        # Handle cookie
        self.preflight()
        self.handle_session_cookie()

        self.set_header('Content-Type', 'application/javascript; charset=UTF-8')

        # Send prelude and flush any pending messages
        self.send_message('h' * 2048)
        self.session.flush()

    def send_message(self, message):
        self.write(message + '\n')
        self.flush()

        # TODO: Close connection based on amount of data transferred
