import time
import hashlib

from tornado.web import asynchronous

from sockjs.tornado.basehandler import BaseHandler, PreflightHandler

IFRAME_TEXT = '''<!DOCTYPE html>
<html>
<head>
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <script>
    document.domain = document.domain;
    _sockjs_onload = function(){SockJS.bootstrap_iframe();};
  </script>
  <script src="%s"></script>
</head>
<body>
  <h2>Don't panic!</h2>
  <p>This is a SockJS hidden iframe. It's used for cross domain magic.</p>
</body>
</html>'''.strip()


class IFrameHandler(BaseHandler):
    def initialize(self, server):
        self.server = server

    def get(self):
        data = IFRAME_TEXT % self.server.settings['sockjs_url']

        hsh = hashlib.md5(data).hexdigest()

        value = self.request.headers.get('If-None-Match')
        if value:
            if value.find(hsh) != -1:
                # TODO: Fix me? Right now it is a hack to remove content-type
                # header
                self.clear()
                del self._headers['Content-Type']

                self.set_status(304)
                return

        self.enable_cache()

        self.set_header('Etag', hsh)
        self.write(data)


class GreetingsHandler(BaseHandler):
    def initialize(self, server):
        self.server = server

    def get(self):
        self.enable_cache()

        self.set_header('Content-Type', 'text/plain; charset=UTF-8')
        self.write('Welcome to SockJS!\n')


class ChunkingTestHandler(PreflightHandler):
    steps = [0.005, 0.025, 0.125, 0.625, 3.125]

    def initialize(self, server):
        self.server = server
        self.step = 0
        self.io_loop = server.io_loop

    @asynchronous
    def post(self):
        self.preflight()
        self.set_header('Content-Type', 'application/javascript; charset=UTF-8')

        self.write('h\n')
        self.flush()

        self.write(' ' * 2048 + 'h\n')
        self.flush()

        def run_step():
            try:
                self.write('h\n')
                self.flush()

                self.step += 1
                if self.step < len(self.steps):
                    self.io_loop.add_timeout(time.time() + self.steps[self.step],
                                             run_step)
                else:
                    self.finish()
            except IOError:
                pass

        self.io_loop.add_timeout(time.time() + self.steps[0], run_step)
