# -*- coding: utf-8 -*-
#
# Copyright: (c) 2011 by the Serge S. Koval, see AUTHORS for more details.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
    sockjs.tornado.flashserver
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements customized PeriodicCallback from tornado with
    support of the sliding window.
"""
import time
import logging


class Callback(object):
    """Custom implementation of the Tornado.Callback with support
    of callback timeout delays.
    """
    def __init__(self, callback, callback_time, io_loop):
        """Constructor.

        `callback`
            Callback function
        `callback_time`
            Callback timeout value (in milliseconds)
        `io_loop`
            io_loop instance
        """
        self.callback = callback
        self.callback_time = callback_time
        self.io_loop = io_loop
        self._running = False

        self.next_run = None

    def calculate_next_run(self):
        """Caltulate next scheduled run"""
        return time.time() + self.callback_time / 1000.0

    def start(self, timeout=None):
        """Start callbacks"""
        self._running = True

        if timeout is None:
            timeout = self.calculate_next_run()

        self.io_loop.add_timeout(timeout, self._run)

    def stop(self):
        """Stop callbacks"""
        self._running = False

    def delay(self):
        """Delay callback"""
        self.next_run = self.calculate_next_run()

    def _run(self):
        if not self._running:
            return

        # Support for shifting callback window
        if self.next_run is not None and time.time() < self.next_run:
            self.start(self.next_run)
            self.next_run = None
            return

        next_call = None
        try:
            next_call = self.callback()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            logging.error("Error in periodic callback", exc_info=True)

        if self._running:
            self.start(next_call)
