import urllib

from tornado.web import asynchronous

from sockjs.tornado import proto
from sockjs.tornado.transports import pollingbase, xhr


class JSONPTransport(xhr.XhrPollingTransport):
    @asynchronous
    def get(self, session_id):
        # Start response
        self.handle_session_cookie()
        self.disable_cache()

        # Grab callback parameter
        self.callback = self.get_argument('c', None)
        if not self.callback:
            self.write('"callback" parameter required')
            self.set_status(500)
            self.finish()
            return

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
        msg = '%s(%s);\r\n' % (self.callback, proto.json_dumps(message))

        self.set_header('Content-Type', 'application/javascript; charset=UTF-8')
        self.set_header('Content-Length', len(msg))

        self.write(msg)

        self._detach()

        self.finish()


class JSONPSendHandler(pollingbase.PollingTransportBase):
    def post(self, session_id):
        self.preflight()

        session = self._get_session(session_id)

        if session is None:
            self.set_status(404)
            return

        #data = self.request.body.decode('utf-8')
        data = self.request.body

        ctype = self.request.headers.get('Content-Type', '').lower()
        if ctype == 'application/x-www-form-urlencoded':
            if not data.startswith('d='):
                self.write("Payload expected.")
                self.set_status(500)
                return

            data = urllib.unquote_plus(data[2:])

        print '$$$$', ctype, data

        if not data:
            self.write("Payload expected.")
            self.set_status(500)
            return

        try:
            messages = proto.json_load(data)

            print 'xxxx', messages
        except:
            # TODO: Proper error handling
            self.write("Broken JSON encoding.")
            self.set_status(500)
            return

        for m in messages:
            session.on_message(m)

        self.write('ok')
        self.set_status(200)
