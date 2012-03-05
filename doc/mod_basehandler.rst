``sockjs.tornado.basehandler``
==============================

.. automodule:: sockjs.tornado.basehandler

    Base Request Handler
    --------------------

    .. autoclass:: BaseHandler

    .. automethod:: BaseHandler.initialize

    Stats
    ^^^^^

    .. automethod:: BaseHandler.prepare
    .. automethod:: BaseHandler._log_disconnect
    .. automethod:: BaseHandler.finish
    .. automethod:: BaseHandler.on_connection_close

    Cache
    ^^^^^

    .. automethod:: BaseHandler.enable_cache
    .. automethod:: BaseHandler.disable_cache
    .. automethod:: BaseHandler.handle_session_cookie

    State
    ^^^^^

    .. automethod:: BaseHandler.safe_finish

    Preflight handler
    -----------------

    .. autoclass:: PreflightHandler

    Handler
    ^^^^^^^

    .. automethod:: PreflightHandler.options

    Helpers
    ^^^^^^^

    .. automethod:: PreflightHandler.preflight
    .. automethod:: PreflightHandler.verify_origin
