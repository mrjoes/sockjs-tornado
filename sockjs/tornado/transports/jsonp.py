from tornado import asynchronous

from sockjs.tornado.transports import pollingbase, proto


class JSONPTransport(pollingbase.PollingTransportBase):
    @asynchronous
    def get(self, session_id):
        self.session = self._get_or_create_session(session_id)

        if not self.session.set_handler(self):
            self.finish()
            return

        if not self.session.send_queue:
            self.session.reset_heartbeat()
        else:
            self.session.flush()

    def send_message(self, message):
        msg = 'callback("%s");\r\n' % proto.json_dumps(message)

        self.preflight()
        self.set_header('Content-Type', 'application/javascript; charset=UTF-8')
        self.set_header('Content-Length', len(message))

        self.write(msg)

        self._detach()

        self.finish()


class JSONPSendHandler(pollingbase.PreflightHandler):
    def post(self, session_id):
        self.preflight()

        session = self._get_session(session_id)

        if session is None:
            self.set_status(404)
            return

        #data = self.request.body.decode('utf-8')
        data = self.request.body
        if not data or not data.startswith('d='):
            self.write("Payload expected.")
            self.set_status(500)
            return

        try:
            messages = proto.json_load(data[2:])
        except:
            # TODO: Proper error handling
            self.write("Broken JSON encoding")
            self.set_status(500)
            return

        for m in messages:
            session.on_message(m)

        self.write('ok')
        self.set_status(200)
