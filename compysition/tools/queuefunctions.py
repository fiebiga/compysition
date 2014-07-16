#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  queuefunctions.py
#
#  Copyright 2013 Jelle Smet <development@smetj.net>
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
#

from compysition.tools import CompysitionQueue

class QueueFunctions(object):

    def __init__(self, *args, **kwargs):
        from compysition.tools import QueuePool
        self.queuepool=QueuePool()

    def createQueue(self, name, max_size=0, type="EVENT"):
        '''Creates a queue in <self.queuepool> named <name> with a size of <max_size>'''

        try:
            setattr(self.queuepool, name, CompysitionQueue(max_size, name, type=type))
            self.logging.info('Created module {0} queue named {1} with max_size {2}.'.format(type, name, max_size))
        except Exception as err:
            self.logging.warn('I could not create the queue named {0}. Reason: {1}'.format(name, err))

    def deleteQueue(self, name):
        '''Deletes the <name> queue from <self.queuepool>.'''

        try:
            del self.queuepool.__dict__[name]
            self.logging.info('Deleted module queue named {0}.'.format(name))
        except Exception as err:
            self.logging.warn('Problem deleting queue {0}.  Reason: {1}.'.format(name, err))