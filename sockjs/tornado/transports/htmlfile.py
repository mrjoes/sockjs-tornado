from tornado import asynchronous

from sockjs.tornado.transports import pollingbase, proto

HTMLFILE_HEAD = r'''
<!doctype html>
<html><head>
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
</head><body><h2>Don't panic!</h2>
  <script>
    document.domain = document.domain;
    var c = parent.%s;
    c.start();
    function p(d) {c.message(d);};
    window.onload = function() {c.stop();};
  </script>
'''.strip()


class HtmlFileTransport(pollingbase.PollingTransportBase):
    @asynchronous
    def get(self, session_id):
        self.session = self._get_or_create_session(session_id)

        if not self.session.set_handler(self):
            self.finish()
            return

        # Start response
        self.preflight()
        self.set_header('Content-Type', 'text/html; charset=UTF-8')

        # TODO: Fix me
        self.write(HTMLFILE_HEAD % 'callback')

        self.flush()

    def send_message(self, message):
        self.write('<script>\np("%s");\n</script>\r\n' % proto.json_dumps(message))

        # TODO: Close connection based on amount of data transferred
