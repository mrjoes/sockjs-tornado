from tornado import websocket, escape


class SockJSWebSocketHandler(websocket.WebSocketHandler):
    def abort_connection(self):
        self.ws_connection._abort()

    def _execute(self, transforms, *args, **kwargs):
        # Websocket only supports GET method
        if self.request.method != "GET":
            self.stream.write(escape.utf8(
                "HTTP/1.1 405 Method Not Allowed\r\n"
                "Allow: GET\r\n"
                "Connection: Close\r\n"
                "\r\n"
            ))
            self.stream.close()
            return

        # Upgrade header should be present and should be equal to WebSocket
        if self.request.headers.get("Upgrade", "").lower() != "websocket":
            self.stream.write(escape.utf8(
                "HTTP/1.1 400 Bad Request\r\n"
                "Connection: Close\r\n"
                "\r\n"
                "Can \"Upgrade\" only to \"WebSocket\"."
            ))
            self.stream.close()
            return

        # Connection header should be upgrade. Some proxy servers/load balancers
        # might mess with it.
        headers = self.request.headers
        connection = map(lambda s: s.strip().lower(), headers.get("Connection", "").split(","))
        if "upgrade" not in connection:
            self.stream.write(escape.utf8(
                "HTTP/1.1 400 Bad Request\r\n"
                "Connection: Close\r\n"
                "\r\n"
                "\"Connection\" must be \"Upgrade\"."
            ))
            self.stream.close()
            return

        return super(SockJSWebSocketHandler, self)._execute(transforms, *args, **kwargs)
