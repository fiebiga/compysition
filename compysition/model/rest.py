#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  rest.py
#
#  Copyright 2015 Adam Fiebig <fiebig.adam@gmail.com>
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

from compysition.event import CompysitionEvent


class RestEntityModel(object):
    """
    Abstract model class
    """

    url_key = "default"
    parents = []
    is_collection = False
    url_key_property = None

    def __init__(self, *args, **kwargs):
        self.properties = {}


