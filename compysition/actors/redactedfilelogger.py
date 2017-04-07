#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       stdout.py
#
#       Copyright 2014 Adam Fiebig fiebig.adam@gmail.com
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#
#

from filelogger import FileLogger
import re

class RedactedFileLogger(FileLogger):

    """
    **Redacts sensitive information from file logger based on provided rules**

    Any regular expression groups identified from the provided patterns that are present in the event data, will be replaced
    with 'REDACTED'. This is indended to ensure file based logging does not contain sensitive information (if patterns are configured properly)

    As an example, sending ['<first_name>(.*?)</first_name>'] as the patterns parameter, will replace whatever the group
    (.*?) finds, with REDACTED. The result would be <first_name>REDACTED</first_name> in the file log.

    Parameters:

    - name (str):                       The instance name
    - patterns (list):            List of patterns to replace. It will replace regex groups within the pattern with 'REDACTED'
    - log file config :                   Kwargs from the app logfile configuration.

    """

    #
    def __init__(self, name, patterns, *args, **kwargs):
        super(RedactedFileLogger, self).__init__(name, *args, **kwargs)
        self.patterns = patterns

    def _process_redaction(self, event):
        for pattern in self.patterns:
            event.message = re.sub(pattern, self._redact_message, event.message)
        return event

    @staticmethod
    def _redact_message(match_object):
        return match_object.group(0).replace(match_object.group(1), 'REDACTED')

    def consume(self, event, *args, **kwargs):
        event = self._process_redaction(event)
        self._process_log_entry(event)