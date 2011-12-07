from tornado import asynchronous

from sockjs.tornado.transports import pollingbase


class XhrStreamingTransport(pollingbase.PollingTransportBase):
    @asynchronous
    def post(self, session_id):
        self.session = self._get_or_create_session(session_id)

        if not self.session.set_handler(self):
            self.finish()
            return

        # Start response
        self.preflight()
        self.set_header('Content-Type', 'application/javascript; charset=UTF-8')

        # Send prelude
        self.send_message('h' * 2048)

    def send_message(self, message):
        self.write(message + '\n')

        # TODO: Close connection based on amount of data transferred
