#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  wsgi.py
#
#  Copyright 2014 James Hulett <james.hulett@cuanswers.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#

from uuid import uuid4 as uuid
from gevent.queue import Queue

class ManagedQueue(object):
    pool = {}

    def __init__(self, label=None, *args, **kwargs):
        self.label = label or uuid().get_hex()
        if not self.pool.get(self.label, None):
            self.pool.update({self.label: {"q":Queue(), "refs":1}})
        else:
            self.pool[self.label]["refs"] += 1

    def __iter__(self):
        return self.pool[self.label]["q"].__iter__()

    def __getattr__(self, attr):
        return getattr(self.pool[self.label]["q"], attr)

    def close(self, *args, **kwargs):
        try:
            self.pool[self.label]["refs"] -= 1
            self.clean()
        except KeyError:  # Means there is nothing the pool for that instance
            pass

    def clean(self):
        if self.pool[self.label]["refs"] < 1:
            del(self.pool[self.label])

    def __del__(self):
        self.close()
