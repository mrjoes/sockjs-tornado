``sockjs.tornado.session``
==========================

Base Session
------------

.. automodule:: sockjs.tornado.session

    .. autoclass:: BaseSession

    Constructor
    ^^^^^^^^^^^

    .. automethod:: BaseSession.__init__

    Handlers
    ^^^^^^^^

    .. automethod:: BaseSession.set_handler
    .. automethod:: BaseSession.verify_state
    .. automethod:: BaseSession.remove_handler

    Messaging
    ^^^^^^^^^

    .. automethod:: BaseSession.send_message
    .. automethod:: BaseSession.send_jsonified
    .. automethod:: BaseSession.broadcast

    State
    ^^^^^

    .. automethod:: BaseSession.close
    .. automethod:: BaseSession.delayed_close
    .. autoattribute:: BaseSession.is_closed
    .. automethod:: BaseSession.get_close_reason


	Connection Session
	------------------

    .. autoclass:: Session

    Constructor
    ^^^^^^^^^^^

    .. automethod:: Session.__init__

    Session
    ^^^^^^^

    .. automethod:: Session.on_delete

    Handlers
    ^^^^^^^^

    .. automethod:: Session.set_handler
    .. automethod:: Session.verify_state
    .. automethod:: Session.remove_handler

    Messaging
    ^^^^^^^^^

    .. automethod:: Session.send_message
    .. automethod:: Session.send_jsonified
    .. automethod:: Session.on_messages

    State
    ^^^^^

    .. automethod:: Session.flush
    .. automethod:: Session.close

    Heartbeats
    ^^^^^^^^^^

    .. automethod:: Session.start_heartbeat
    .. automethod:: Session.stop_heartbeat
    .. automethod:: Session.delay_heartbeat
    .. automethod:: Session._heartbeat


Utilities
---------

    .. autoclass:: ConnectionInfo