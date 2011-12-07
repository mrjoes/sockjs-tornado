from tornado.web import asynchronous

from sockjs.tornado import proto
from sockjs.tornado.transports import pollingbase


class XhrPollingTransport(pollingbase.PollingTransportBase):
    name = 'xhr-polling'

    @asynchronous
    def post(self, session_id):
        self.session = self._get_or_create_session(session_id)

        # Assign handler but do not start heartbeats
        if not self.session.set_handler(self, False):
            self.finish()
            return

        if not self.session.send_queue:
            self.session.reset_heartbeat()
        else:
            self.session.flush()

    def send_message(self, message):
        self.preflight()
        self.handle_session_cookie()

        self.set_header('Content-Type', 'text/plain; charset=UTF-8')
        self.set_header('Content-Length', len(message))
        self.write(message)

        self._detach()

        self.finish()


class XhrSendHandler(pollingbase.PreflightHandler):
    def post(self, session_id):
        self.preflight()

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
            self.write("Broken JSON encoding")
            self.set_status(500)
            return

        for m in messages:
            session.on_message(m)

        self.set_status(204)
