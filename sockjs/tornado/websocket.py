# -*- coding: utf-8 -*-
"""
    sockjs.tornado.websocket
    ~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains modified version of the WebSocketHandler from
    Tornado with some performance fixes and behavior changes for Hybi10
    protocol.

    Server-side implementation of the WebSocket protocol.

    `WebSockets <http://dev.w3.org/html5/websockets/>`_ allow for bidirectional
    communication between the browser and server.

    .. warning::

       The WebSocket protocol is still in development.  This module
       currently implements the "hixie-76", "hybi-10", and "hybi-17"
       versions of the protocol.  See this `browser compatibility table
       <http://en.wikipedia.org/wiki/WebSockets#Browser_support>`_ on
       Wikipedia.
"""
# Author: Jacob Kristhammar, 2010

import functools
import hashlib
import logging
import struct
import time
import base64
import tornado.escape
import tornado.web

from tornado import stack_context, websocket
from tornado.util import bytes_type, b


class WebSocketHandler(websocket.WebSocketHandler):
    def _execute(self, transforms, *args, **kwargs):
        self.open_args = args
        self.open_kwargs = kwargs

        # Websocket only supports GET method
        with stack_context.ExceptionStackContext(self._handle_websocket_exception):
            # Websocket only supports GET method
            if self.request.method != 'GET':
                self.stream.write(tornado.escape.utf8(
                    "HTTP/1.1 405 Method Not Allowed\r\n\r\n"
                ))
                self.stream.close()
                return

            # Upgrade header should be present and should be equal to WebSocket
            if self.request.headers.get("Upgrade", "").lower() != 'websocket':
                self.stream.write(tornado.escape.utf8(
                    "HTTP/1.1 400 Bad Request\r\n\r\n"
                    "Can \"Upgrade\" only to \"WebSocket\"."
                ))
                self.stream.close()
                return

            # Connection header should be upgrade. Some proxy servers/load balancers
            # might mess with it.
            headers = self.request.headers
            connection = map(lambda s: s.strip().lower(), headers.get("Connection", "").split(","))
            if 'upgrade' not in connection:
                self.stream.write(tornado.escape.utf8(
                    "HTTP/1.1 400 Bad Request\r\n\r\n"
                    "\"Connection\" must be \"Upgrade\"."
                ))
                self.stream.close()
                return

            # Handle proper protocol version
            if self.request.headers.get("Sec-WebSocket-Version") in ("7", "8", "13"):
                self.ws_connection = WebSocketProtocol8(self)
                self.ws_connection.accept_connection()

            elif self.request.headers.get("Sec-WebSocket-Version"):
                self.stream.write(tornado.escape.utf8(
                    "HTTP/1.1 426 Upgrade Required\r\n"
                    "Sec-WebSocket-Version: 8\r\n\r\n"))
                self.stream.close()

            else:
                self.ws_connection = websocket.WebSocketProtocol76(self)
                self.ws_connection.accept_connection()

    def _handle_websocket_exception(self, type, value, traceback):
        # Silently ignore IOError, because tornado will call on_close for us
        # and we don't want to spam log with Tracebacks
        if type is IOError:
            return True

    def abort_connection(self):
        self.ws_connection._abort()


class WebSocketProtocol8(websocket.WebSocketProtocol):
    """Implementation of the WebSocket protocol, version 8 (draft version 10).

    Compare
    http://tools.ietf.org/html/draft-ietf-hybi-thewebsocketprotocol-10
    """
    STRUCT_BB = struct.Struct("BB")
    STRUCT_BBH = struct.Struct("!BBH")
    STRUCT_BBQ = struct.Struct("!BBQ")
    STRUCT_H = struct.Struct("!H")
    STRUCT_Q = struct.Struct("!Q")

    def __init__(self, handler, auto_decode=False):
        websocket.WebSocketProtocol.__init__(self, handler)
        self._final_frame = False
        self._frame_opcode = None
        self._frame_mask = None
        self._frame_length = None
        self._fragmented_message_buffer = None
        self._fragmented_message_opcode = None
        self._started_closing_handshake = False

        self._auto_decode = auto_decode

    def accept_connection(self):
        try:
            self._handle_websocket_headers()
            self._accept_connection()
        except ValueError:
            logging.debug("Malformed WebSocket request received")
            self._abort()
            return

    def _handle_websocket_headers(self):
        """Verifies all invariant- and required headers

        If a header is missing or have an incorrect value ValueError will be
        raised
        """
        fields = ("Host", "Sec-Websocket-Key", "Sec-Websocket-Version")
        if not all(map(lambda f: self.request.headers.get(f), fields)):
            raise ValueError("Missing/Invalid WebSocket headers")

    def _challenge_response(self):
        sha1 = hashlib.sha1()
        sha1.update(tornado.escape.utf8(
                self.request.headers.get("Sec-Websocket-Key")))
        sha1.update(b("258EAFA5-E914-47DA-95CA-C5AB0DC85B11")) # Magic value
        return tornado.escape.native_str(base64.b64encode(sha1.digest()))

    def _accept_connection(self):
        self.stream.write(tornado.escape.utf8(
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            "Sec-WebSocket-Accept: %s\r\n\r\n" % self._challenge_response()))

        self.handler.open(*self.handler.open_args, **self.handler.open_kwargs)
        self._receive_frame()

    def _write_frame(self, fin, opcode, data):
        if fin:
            finbit = opcode | 0x80
        else:
            finbit = opcode

        l = len(data)
        if l < 126:
            frame = self.STRUCT_BB.pack(finbit, l)
        elif l <= 0xFFFF:
            frame = self.STRUCT_BBH.pack(finbit, 126, l)
        else:
            frame = self.STRUCT_BBQ.pack(finbit, 127, l)
        frame += data
        self.stream.write(frame)

    def write_message(self, message, binary=False):
        """Sends the given message to the client of this Web Socket."""
        if isinstance(message, dict):
            message = tornado.escape.json_encode(message)
        if isinstance(message, unicode):
            message = message.encode("utf-8")
        assert isinstance(message, bytes_type)
        if not binary:
            opcode = 0x1
        else:
            opcode = 0x2
        self._write_frame(True, opcode, message)

    def _receive_frame(self):
        self.stream.read_bytes(2, self._on_frame_start)

    def _on_frame_start(self, data):
        header, payloadlen = self.STRUCT_BB.unpack(data)

        self._final_frame = header & 0x80
        self._frame_opcode = header & 0xf

        if not (payloadlen & 0x80):
            # Unmasked frame -> abort connection
            self._abort()

        payloadlen = payloadlen & 0x7f

        if payloadlen < 126:
            self._frame_length = payloadlen
            self.stream.read_bytes(4, self._on_masking_key)
        elif payloadlen == 126:
            self.stream.read_bytes(2, self._on_frame_length_16)
        elif payloadlen == 127:
            self.stream.read_bytes(8, self._on_frame_length_64)

    def _on_frame_length_16(self, data):
        self._frame_length = self.STRUCT_H.unpack(data)[0]
        self.stream.read_bytes(4, self._on_masking_key)

    def _on_frame_length_64(self, data):
        self._frame_length = self.STRUCT_Q.unpack(data)[0]
        self.stream.read_bytes(4, self._on_masking_key)

    def _on_masking_key(self, data):
        self._frame_mask = bytearray(data)
        self.stream.read_bytes(self._frame_length, self._on_frame_data)

    def _on_frame_data(self, data):
        unmasked = bytearray(data)
        mask = self._frame_mask
        for i in xrange(len(unmasked)):
            unmasked[i] = unmasked[i] ^ mask[i % 4]

        if not self._final_frame:
            if self._fragmented_message_buffer:
                self._fragmented_message_buffer += unmasked
            else:
                self._fragmented_message_opcode = self._frame_opcode
                self._fragmented_message_buffer = unmasked
        else:
            if self._frame_opcode == 0:
                unmasked = self._fragmented_message_buffer + unmasked
                opcode = self._fragmented_message_opcode
                self._fragmented_message_buffer = None
            else:
                opcode = self._frame_opcode

            self._handle_message(opcode, bytes_type(unmasked))

        if not self.client_terminated:
            self._receive_frame()

    def _handle_message(self, opcode, data):
        if self.client_terminated:
            return

        if opcode == 0x1:
            # UTF-8 data
            if self._auto_decode:
                self.handler.on_message(data.decode("utf-8", "replace"))
            else:
                self.handler.on_message(data)
        elif opcode == 0x2:
            # Binary data
            self.handler.on_message(data)
        elif opcode == 0x8:
            # Close
            self.client_terminated = True
            if not self._started_closing_handshake:
                self._write_frame(True, 0x8, b(""))
            self.stream.close()
        elif opcode == 0x9:
            # Ping
            self._write_frame(True, 0xA, data)
        elif opcode == 0xA:
            # Pong
            pass
        else:
            self._abort()

    def close(self):
        """Closes the WebSocket connection."""
        self._write_frame(True, 0x8, b(""))
        self._started_closing_handshake = True
        self._waiting = tornado.ioloop.IOLoop.instance().add_timeout(time.time() + 5, self._abort)

