from tornado.web import asynchronous

from sockjs.tornado import proto
from sockjs.tornado.transports import pollingbase


class XhrPollingTransport(pollingbase.PollingTransportBase):
    @asynchronous
    def post(self, session_id):
        # Start response
        self.preflight()
        self.handle_session_cookie()

        # Get or create session without starting heartbeat
        if not self._attach_session(session_id, False):
            return

        if not self.session:
            return

        if not self.session.send_queue:
            self.session.start_heartbeat()
        else:
            self.session.flush()

    def send_pack(self, message):
        self.set_header('Content-Type', 'application/javascript; charset=UTF-8')
        self.set_header('Content-Length', len(message) + 1)
        self.write(message + '\n')

        self._detach()

        self.finish()


class XhrSendHandler(pollingbase.PollingTransportBase):
    name = 'xhr-polling'

    def post(self, session_id):
        self.preflight()
        self.handle_session_cookie()

        session = self._get_session(session_id)

        if session is None:
            self.set_status(404)
            return

        #data = self.request.body.decode('utf-8')
        data = self.request.body
        if not data:
            self.write("Payload expected.")
            self.set_status(500)
            return

        try:
            messages = proto.json_load(data)
        except:
            # TODO: Proper error handling
            self.write("Broken JSON encoding.")
            self.set_status(500)
            return

        for m in messages:
            session.on_message(m)

        self.set_status(204)
        self.set_header('Content-Type', 'text/plain')
