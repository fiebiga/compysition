#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  importing.py
#
#  Copyright 2013 Jelle Smet <development@smetj.net>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
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


class TestImport():
    '''py.test tests dealing with importing various parts of
    compysition'''

    def testCompysition(self):
        try:
            import compysition
        except:
            assert compysition

    def testCompysitionBootstrap(self):
        try:
            from compysition.bootstrap import PidHandling
        except:
            assert PidHandling

        try:
            from compysition.bootstrap import ModuleHandling
        except:
            assert ModuleHandling

        try:
            from compysition.bootstrap import Initialize
        except:
            assert Initialize

        try:
            from compysition.bootstrap import Start
        except:
            assert Start

        try:
            from compysition.bootstrap import Debug
        except:
            assert Debug

        try:
            from compysition.bootstrap import Stop
        except:
            assert Stop

        try:
            from compysition.bootstrap import Kill
        except:
            assert Kill

        try:
            from compysition.bootstrap import List
        except:
            assert List

        try:
            from compysition.bootstrap import Show
        except:
            assert Show

        try:
            from compysition.bootstrap import Dispatch
        except:
            assert Dispatch

        try:
            from compysition.bootstrap import BootStrap
        except:
            assert BootStrap

    def testCompysitionErrors(self):

        try:
            from compysition.errors import QueueEmpty
        except:
            assert QueueEmpty

        try:
            from compysition.errors import QueueFull
        except:
            assert QueueFull

        try:
            from compysition.errors import QueueLocked
        except:
            assert QueueLocked

        try:
            from compysition.errors import QueueMissing
        except:
            assert QueueMissing

        try:
            from compysition.errors import QueueOccupied
        except:
            assert QueueOccupied

        try:
            from compysition.errors import SetupError
        except:
            assert SetupError

    def testCompysitionModule(self):

        try:
            from compysition.module import Fanout
        except:
            assert Fanout

        try:
            from compysition.module import Funnel
        except:
            assert Funnel

        try:
            from compysition.module import Graphite
        except:
            assert Graphite

        try:
            from compysition.module import Header
        except:
            assert Header

        try:
            from compysition.module import HumanLogFormatter
        except:
            assert HumanLogFormatter

        try:
            from compysition.module import LockBuffer
        except:
            assert LockBuffer

        try:
            from compysition.module import Null
        except:
            assert Null

        try:
            from compysition.module import RoundRobin
        except:
            assert RoundRobin

        try:
            from compysition.module import STDOUT
        except:
            assert STDOUT

        try:
            from compysition.module import TestEvent
        except:
            assert TestEvent

        try:
            from compysition.module import TippingBucket
        except:
            assert TippingBucket

        try:
            from compysition.module import Syslog
        except:
            assert Syslog

    def testCompysitionRouter(self):
        try:
            from compysition.router import Default
        except:
            assert Default

    def testCompysitionTools(self):

        try:
            from compysition.tools import QueueFunctions
        except:
            assert QueueFunctions

        try:
            from compysition.tools import LoopContextSwitcher
        except:
            assert LoopContextSwitcher

        try:
            from compysition.tools import Consumer
        except:
            assert Consumer

        try:
            from compysition.tools import QLogging
        except:
            assert QLogging

        try:
            from compysition.tools import QueuePool
        except:
            assert QueuePool

        try:
            from compysition.tools import Measure
        except:
            assert Measure

