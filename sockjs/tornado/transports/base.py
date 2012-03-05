from sockjs.tornado import session


class BaseTransportMixin(object):
    name = 'override_me_please'

    def get_conn_info(self):
        return session.ConnectionInfo(self.request.remote_ip,
                                      self.request.cookies,
                                      self.request.arguments)

    def session_closed(self):
        pass
