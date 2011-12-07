from tornado.web import asynchronous

from sockjs.tornado.transports import pollingbase


class EventSourceTransport(pollingbase.PollingTransportBase):
    name = 'eventsource'

    @asynchronous
    def get(self, session_id):
        # Start response
        self.preflight()
        self.handle_session_cookie()
        self.disable_cache()

        self.set_header('Content-Type', 'text/event-stream; charset=UTF-8')
        self.write('\r\n')
        self.flush()

        if not self._attach_session(session_id):
            self.finish()
            return

        if self.session is not None:
            self.session.flush()

    def send_pack(self, message):
        self.write('data: %s\r\n\r\n' % message)
        self.flush()

        # TODO: Close connection based on amount of data transferred
