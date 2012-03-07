Statistics
==========

sockjs-tornado captures some counters:

==================== =================================================
Name                 Description
==================== =================================================
**Sessions**
----------------------------------------------------------------------
sessions_active      Number of currently active sessions

**Transports**
----------------------------------------------------------------------
transp_xhr           # of sessions opened with xhr transport
transp_websocket     # of sessions opened with websocket transport
transp_xhr_streaming # of sessions opened with xhr streaming transport
transp_jsonp         # of sessions opened with jsonp transport
transp_eventsource   # of sessions opened with eventsource transport
transp_htmlfile      # of sessions opened with htmlfile transport
transp_rawwebsocket  # of sessions opened with raw websocket transport

**Connections**
----------------------------------------------------------------------
connections_active   Number of currently active connections
connections_ps       Number of opened connections per second

**Packets**
----------------------------------------------------------------------
packets_sent_ps      Packets sent per second
packets_recv_ps      Packets received per second
==================== =================================================

Stats are captured by the router object and can be accessed
through the ``stats`` property::

	MyRouter = SockJSRouter(MyConnection)

	print MyRouter.stats.dump()

For more information, check stats module API or ``stats`` sample.
