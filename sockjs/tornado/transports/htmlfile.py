from tornado.web import asynchronous

from sockjs.tornado import proto
from sockjs.tornado.transports import pollingbase

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
    name = 'htmlfile'

    @asynchronous
    def get(self, session_id):
        # Grab callback parameter
        callback = self.get_argument('c')
        if not callback:
            self.write('"callback" parameter required')
            self.set_status(500)
            self.finish()
            return

        # Now try to attach to session
        self.session = self._get_or_create_session(session_id)

        if not self.session.set_handler(self):
            self.finish()
            return

        # Start response
        self.preflight()
        self.handle_session_cookie()
        self.disable_cache()

        self.set_header('Content-Type', 'text/html; charset=UTF-8')

        # TODO: Fix me - use parameter
        self.write(HTMLFILE_HEAD % callback)
        self.flush()

        # Flush any messages from the session
        self.session.flush()

    def send_message(self, message):
        self.write('<script>\np("%s");\n</script>\r\n' % proto.json_dumps(message))
        self.flush()

        # TODO: Close connection based on amount of data transferred
