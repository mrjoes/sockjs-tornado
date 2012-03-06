``sockjs.tornado.transports.rawwebsocket``
==========================================

.. automodule:: sockjs.tornado.transports.rawwebsocket


.. autoclass:: RawSession

    .. automethod:: send_message
    .. automethod:: on_message


.. autoclass:: RawWebSocketTransport

    .. automethod:: open
    .. automethod:: on_message
    .. automethod:: on_close
    .. automethod:: send_pack

    Sessions
    ^^^^^^^^

    .. automethod:: RawWebSocketTransport.session_closed
    .. automethod:: RawWebSocketTransport._detach
