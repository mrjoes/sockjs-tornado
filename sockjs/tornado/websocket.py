from tornado import websocket, escape

try:
    from urllib.parse import urlparse # py3
except ImportError:
    from urlparse import urlparse # py2


class SockJSWebSocketHandler(websocket.WebSocketHandler):

    def check_origin(self, origin):
        # let tornado first check if connection from the same domain
        same_domain = super(SockJSWebSocketHandler, self).check_origin(origin)
        if same_domain:
            return True

        # this is cross-origin connection - check using SockJS server settings
        allow_origin = self.server.settings.get("websocket_allow_origin", "*")
        if allow_origin == "*":
            return True
        else:
            parsed_origin = urlparse(origin)
            origin = parsed_origin.netloc
            origin = origin.lower()
            return origin in allow_origin

    def abort_connection(self):
        self.ws_connection._abort()

    def _execute(self, transforms, *args, **kwargs):
        self._transforms = transforms
        # Websocket only supports GET method
        if self.request.method != "GET":
            self.set_status(405)
            self.finish(escape.utf8(
                "Allow: GET\r\n"
                "Connection: Close\r\n"
                "\r\n"
            ))
            return

        # Upgrade header should be present and should be equal to WebSocket
        if self.request.headers.get("Upgrade", "").lower() != "websocket":
            self.set_status(400)
            self.finish(escape.utf8(
                "Connection: Close\r\n"
                "\r\n"
                "Can \"Upgrade\" only to \"WebSocket\"."
            ))
            return

        # Connection header should be upgrade. Some proxy servers/load balancers
        # might mess with it.
        headers = self.request.headers
        connection = map(lambda s: s.strip().lower(), headers.get("Connection", "").split(","))
        if "upgrade" not in connection:
            self.set_status(400)
            self.finish(escape.utf8(
                "Connection: Close\r\n"
                "\r\n"
                "\"Connection\" must be \"Upgrade\"."
            ))
            return

        return super(SockJSWebSocketHandler, self)._execute(transforms, *args, **kwargs)
