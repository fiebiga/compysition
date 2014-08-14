#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  __init__.py
#
#  Copyright 2014 Adam Fiebig <fiebig.adam@gmail.com>
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

"""
Compysition Specific
"""

from compysition.module.wsgi import WSGI
from compysition.module.echodata import EchoData
from compysition.module.basicauth import BasicAuth
from compysition.module.transformer import Transformer
from compysition.module.xmlaggregator import XMLAggregator
from compysition.module.xmlmatcher import XMLMatcher
from compysition.module.tagaggregator import TagAggregator
from compysition.module.xmlfilter import XMLFilter

"""
All code below here was included in original wishbone project by smetj <development@smetj.net>
"""
from compysition.module.null import Null
from compysition.module.graphite import Graphite
from compysition.module.stdout import STDOUT
from compysition.module.loglevelfilter import LogLevelFilter
from compysition.module.fanout import Fanout
from compysition.module.funnel import Funnel
from compysition.module.header import Header
from compysition.module.tippingbucket import TippingBucket
from compysition.module.lockbuffer import LockBuffer
from compysition.module.humanlogformatter import HumanLogFormatter
from compysition.module.wbsyslog import Syslog
from compysition.module.testevent import TestEvent
from compysition.module.roundrobin import RoundRobin
from compysition.module.slow import Slow
from compysition.module.flowcontroller import FlowController
from compysition.module.filelogger import FileLogger
