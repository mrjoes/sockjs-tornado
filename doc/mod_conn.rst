``sockjs.tornado.conn``
=======================

.. automodule:: sockjs.tornado.conn

	.. autoclass:: SockJSConnection

	Callbacks
	^^^^^^^^^

	.. automethod:: SockJSConnection.on_open
	.. automethod:: SockJSConnection.on_message
	.. automethod:: SockJSConnection.on_close

	Output
	^^^^^^

	.. automethod:: SockJSConnection.send
	.. automethod:: SockJSConnection.broadcast

	Management
	^^^^^^^^^^

	.. automethod:: SockJSConnection.close
	.. autoattribute:: SockJSConnection.is_closed
