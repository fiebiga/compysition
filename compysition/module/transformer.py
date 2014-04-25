#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  transformer.py
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

from compysition import Actor
from pprint import pformat
from lxml import etree
import os
import pdb

class Transformer(Actor):
    '''**Sample module which reverses incoming events.**

    Parameters:

        - name (str):       The instance name.

    Queues:

        - inbox:    Incoming events.
        - outbox:   Outgoing events.
    '''

    def __init__(self, name, xslt_path, *args, **kwargs):
        Actor.__init__(self, name, setupbasic=True)
        self.logging.info("Initialized")
        self.subjects = args or ('XML',)
        self.key = kwargs.get('key', None) or self.name
        self.caller = 'wsgi'

        self.template = self.load_template(xslt_path)

        self.createQueue('errors')

    def consume(self, event, *args, **kwargs):
        #pdb.set_trace()
        try:
            root = etree.Element(self.name)
            #for key in self.subjects:
            #    try:
            #        root.append(etree.XML(event['data'][key]))
            #    except:
            #        self.logging.warn("Subject {0} did not exist in submitted event. Subject was not appended".format(key))

            f = open('{0}_event_root.txt'.format(self.key),'w')
            f.write(b"{0}".format(etree.tostring(root))) # python will convert \n to os.linesep
            f.close() # you can omit in most cases as the destructor will call if
            print("Adding {0} Key to template".format(self.key))
            #event['data'][self.key] = etree.tostring(self.template(root))
            event['data'] = etree.tostring(self.template(root))
            #self.queuepool.outbox.put(event)
            self.send_event(event)
        except KeyError:
            self.logging.info("{} could not find the form subject {} in event {}".format(self.name, self.subjects, event))
            event['header'].get(self.caller, {}).update({'status': '400 Bad Request'})
            event['data'] = "Malformed Request"
            self.queuepool.errors.put(event)

        f = open('{0}_event.txt'.format(self.key),'w')
        f.write(b"{0}".format(event)) # python will convert \n to os.linesep
        f.close() # you can omit in most cases as the destructor will call if

    def transform(self, etree_element):
        return self.template(etree_element)

    def load_template(self, path):
        try:
            return etree.XSLT(etree.parse(path))
        except Exception as e:
            self.logging.error("Unable to load XSLT at {}:{}".format(path, e))

    def load_templates(self):
        directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.__class__.__name__.lower(), self.service.lower())
        for file_name in os.listdir(directory):
            base_name = os.path.splitext(file_name)[0]
            file_path = os.path.join(directory, file_name)
            xslt = etree.XSLT(etree.parse(file_path))
            self.templates.update({base_name: xslt})