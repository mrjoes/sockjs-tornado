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

HTMLFILE_HEAD += ' ' * (1024 - len(HTMLFILE_HEAD) + 14)
HTMLFILE_HEAD += '\r\n\r\n'


class HtmlFileTransport(pollingbase.PollingTransportBase):
    name = 'htmlfile'

    @asynchronous
    def get(self, session_id):
        # Start response
        self.preflight()
        self.handle_session_cookie()
        self.disable_cache()
        self.set_header('Content-Type', 'text/html; charset=UTF-8')

        # Grab callback parameter
        callback = self.get_argument('c', None)
        if not callback:
            self.write('"callback" parameter required')
            self.set_status(500)
            self.finish()
            return

        # TODO: Fix me - use parameter
        self.write(HTMLFILE_HEAD % callback)
        self.flush()

        # Now try to attach to session
        if not self._attach_session(session_id):
            self.finish()
            return

        # Flush any pending messages
        if not self.detached:
            self.session.flush()

    def send_pack(self, message):
        # TODO: Just do escaping
        self.write('<script>\np(%s);\n</script>\r\n' % proto.json_encode(message))
        self.flush()

        # TODO: Close connection based on amount of data transferred
