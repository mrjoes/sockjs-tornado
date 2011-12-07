from tornado.web import RequestHandler


class BaseHandler(RequestHandler):
    def enable_cache(self):
        self.set_header('Cache-Control', 'max-age=123456, public')
        self.set_header('Expires', 'SOMETIMEINDAFUTURE')
        self.set_header('access-control-max-age', '123456')

    def disable_cache(self):
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')

    def handle_session_cookie(self):
        cookie = self.cookies.get('JSESSIONID')
        if not cookie:
            cookie = 'dummy'
        self.set_cookie('JSESSIONID', cookie)

