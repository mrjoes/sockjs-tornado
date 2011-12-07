import datetime

from tornado.web import RequestHandler

CACHE_TIME = 31536000


class BaseHandler(RequestHandler):
    def enable_cache(self):
        self.set_header('Cache-Control', 'max-age=%d, public' % CACHE_TIME)

        d = datetime.datetime.now() + datetime.timedelta(seconds=CACHE_TIME)
        self.set_header('Expires', d.strftime('%a, %d %b %Y %H:%M:%S'))

        self.set_header('access-control-max-age', CACHE_TIME)

    def disable_cache(self):
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')

    def handle_session_cookie(self):
        cookie = self.cookies.get('JSESSIONID')

        if not cookie:
            cv = 'dummy'
        else:
            cv = cookie.value

        self.set_cookie('JSESSIONID', cv)

