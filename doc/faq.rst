Frequently Asked Questions
==========================

How fast is sockjs-tornado?
---------------------------

Long story short, at least for websocket transport:

    1. On CPython it is (or was) comparable to sockjs-node and socket.io (node.js server)
    2. On PyPy 1.7 it was 3x faster than sockjs-node and socket.io

You can find more information `here <http://mrjoes.github.com/2011/12/15/sockjs-bench.html>`_.

Can I use query string parameters or cookies to pass data to the server?
------------------------------------------------------------------------

No, you can not. SockJS does not support application cookies and you can't pass query string parameters.

How do I implement authentication in my application?
----------------------------------------------------

Send packet with authentication token after connecting to the server. In pseudo code it can look like this:

Client side::

    <script language="javascript">
        var sock = new SockJS('/echo');

        // Lets assume we invented simple protocol, where first word is a command name and second is a payload.
        sock.onconnect = function() {
            sock.send('auth,xxx');
            sock.send('echo,bar');
        };
    </script>


Server side::

    class EchoConnection(SockJSConnection):
        def on_open(self, info):
            self.authenticated = False

        def on_message(self, msg):
            pack, data = msg.split(',', 1)

            # Ignore all packets except of 'auth' if user is not yet authenticated
            if not self.authenticated and pack != 'auth':
                return

            if pack == 'auth':
                # Decrypt user_id (or user name - you decide). You might want to add salt to the token as well.
                user_id = des_decrypt(data, secret_key)

                # Validate user_id here by making DB call, etc.
                user = get_user(user_id)

                if user is None and user.is_active:
                    self.send('error,Invalid user!')
                    return

                self.authenticated = True
            elif pack == 'echo':
                self.send(data)


Can I open more than one SockJS connection on same page?
--------------------------------------------------------

No, you can not because of the AJAX restrictions. You have to use
connection multiplexing. Check `multiplex` sample to find out how you can do it.

Can I send python objects through the SockJS?
---------------------------------------------

As SockJS emulates websocket protocol and websocket protocol only supports strings, you can not send arbitrary objects (they won't be JSON serialized automatically). On a side node - SockJS client already includes `JSON2.js` library, so you can use it without any extra dependencies.

How do I scale sockjs-tornado?
------------------------------

Easiest way is to start multiple instances of the sockjs-tornado server (one per core) and load balance them using haproxy. You can find `sample haproxy configuration here <https://github.com/sockjs/sockjs-node/blob/master/examples/haproxy.cfg>`_.

Alternatively, if you already use some kind of load balancer, make sure you enable sticky sessions. sockjs-tornado maintains state for each user and
there's no way to synchronize this state between sockjs-tornado instances.

Also, it is up for you, as a developer, to decide how you're going to synchronize state of the servers in a cluster. You can use `Redis <http://redis.io/>`_ as a meeting point or use `ZeroMQ <http://www.zeromq.org/>`_, etc.
