from datetime import datetime
from collections import deque

from tornado import ioloop


class MovingAverage(object):
    """Moving average class implementation"""
    def __init__(self, period=10):
        """Constructor.

        `period`
            Moving window size. Average will be calculated
            from the data in the window.
        """
        self.period = period
        self.stream = deque()
        self.sum = 0
        self.accumulator = 0
        self.last_average = 0

    def add(self, n):
        """Add value to the current accumulator

        `n`
            Value to add
        """
        self.accumulator += n

    def flush(self):
        """Add accumulator to the moving average queue
        and reset it. For example, called by the StatsCollector
        once per second to calculate per-second average.
        """
        n = self.accumulator
        self.accumulator = 0

        stream = self.stream
        stream.append(n)
        self.sum += n

        streamlen = len(stream)

        if streamlen > self.period:
            self.sum -= stream.popleft()
            streamlen -= 1

        if streamlen == 0:
            self.last_average = 0
        else:
            self.last_average = self.sum / float(streamlen)


class StatsCollector(object):
    def __init__(self, io_loop):
        # Sessions
        self.sess_active = 0

        # Connections
        self.conn_active = 0
        self.conn_ps = MovingAverage()

        # Packets
        self.pack_sent_ps = MovingAverage()
        self.pack_recv_ps = MovingAverage()

        self._callback = ioloop.PeriodicCallback(self._update,
                                                 1000,
                                                 io_loop)
        self._callback.start()

    def _update(self):
        self.conn_ps.flush()

        self.pack_sent_ps.flush()
        self.pack_recv_ps.flush()

    def dump(self):
        return dict(
            # Sessions
            sessions_active=self.sess_active,

            # Connections
            connections_active=self.conn_active,
            connections_ps=self.conn_ps.last_average,

            # Packets
            packets_sent_ps=self.pack_sent_ps.last_average,
            packets_recv_ps=self.pack_recv_ps.last_average
            )

    # Various event callbacks
    def on_conn_opened(self):
        self.conn_active += 1
        self.conn_ps.add(1)

    def on_conn_closed(self):
        self.conn_active -= 1

    def on_pack_sent(self, num):
        self.pack_sent_ps.add(num)

    def on_pack_recv(self, num):
        self.pack_recv_ps.add(num)
