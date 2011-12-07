from sockjs.tornado.basehandler import BaseHandler

IFRAME_TEXT = '''<!DOCTYPE html>
<html>
<head>
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <script>
    document.domain = document.domain;
    _sockjs_onload = function\(\){SockJS.bootstrap_iframe\(\);};
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
        self._enable_cache()

        self.write(IFRAME_TEXT % self.server.settings['sockjs_url'])


class GreetingsHandler(BaseHandler):
    def initialize(self, server):
        self.server = server

    def get(self):
        self._enable_cache()

        self.set_header('Content-Type', 'text/plain; charset=UTF-8')
        self.write('Welcome to SockJS!')
