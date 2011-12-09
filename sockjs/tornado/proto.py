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
    sockjs.tornado.proto
    ~~~~~~~~~~~~~~~~~~~~

    SockJS protocol related functions
"""
import logging

# TODO: Add support for ujson module once they can accept unicode strings

# Try to find best json encoder available
try:
    # Check for simplejson
    import simplejson

    json_encode = lambda data: simplejson.dumps(data, separators=(',', ':'))
    json_decode = lambda data: simplejson.loads(data)

    logging.debug('sockjs.tornado will use simplejson module')
except ImportError:
    # Use slow json
    import json

    logging.debug('sockjs.tornado will use json module')

    json_encode = lambda data: json.dumps(data, separators=(',', ':'))
    json_decode = lambda data: json.loads(data)

# Protocol handlers
CONNECT = 'o'
DISCONNECT = 'c'
MESSAGE = 'm'
HEARTBEAT = 'h'


# Various protocol helpers
def disconnect(code, reason):
    return 'c[%d,"%s"]' % (code, reason)


def encode_messages(messages):
    return 'a%s' % json_encode(messages)


def encode_single_message(msg):
    return 'a[%s]' % json_encode(msg)
