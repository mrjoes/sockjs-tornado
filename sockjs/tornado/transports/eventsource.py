from tornado import asynchronous

from sockjs.tornado.transports import pollingbase


class EventSourceTransport(pollingbase.PollingTransportBase):
    name = 'eventsource'

    @asynchronous
    def get(self, session_id):
        self.session = self._get_or_create_session(session_id)

        if not self.session.set_handler(self):
            self.finish()
            return

        # Start response
        self.preflight()
        self.set_header('Content-Type', 'text/event-stream; charset=UTF-8')

        self.session.flush()

    def send_message(self, message):
        self.write('data: %s\r\n' + message)
        self.flush()

        # TODO: Close connection based on amount of data transferred
