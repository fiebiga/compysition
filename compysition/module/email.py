#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  xmlfilter.py
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

from compysition import Actor
import smtplib
from email.mime.text import MIMEText

class EmailEvent(Actor):
    '''**A module that send an email to any given target with a specific message**

    Parameters:

        - name (str):           The instance name.
        - xpath (str):          The xpath we wish to filter on. If this leads to an element and 'value' is also specified, the text of that element
                                    will be used to evaluate the provided value.
        - value (str):          (Default: None) The value to filter on for the given xpath. 
                                    If unspecified the event will be forwarded if the given xpath element exists at all.
        - blacklist (bool):     (Default: False) Whether or not to use a blacklist for a given 'value'. 
                                    Setting this value to true will cause the module discard the event only if the element value equals the value given.
                                    If no value is set, and blacklist=True, the XMLFilter will discard the event if the xpath element DOES exist

    event = {
        'data': '<some_xml_data></some_xml_data>'

        'header': {
            'wsgi': {
                'request_id': 1
            }
        }
    }
    '''
    
    def __init__(self, name, from_address="no-reply@cuanswers.com", smtp_server='membermail.cuanswers.com', subject="", *args, **kwargs):
        self.from_address = from_address
        self.smtp_server = smtp_server
        self.subject = "New Auto Application Received From RouteOne"

    def consume(self, event, *args, **kwargs):
        msg = MIMEText("Hello Boys")
        recipients = ['adam.fiebig@cuanswers.com']

        msg['Subject'] = self.subject or ""
        msg['To'] = ', '.join(recipients)
        msg['From'] = self.from_address
        s = smtplib.SMTP(self.smtp_server)
        s.sendmail(self.from_address, recipients, msg.as_string())
        s.quit()


ee = EmailEvent("test")
ee.consume("we")
