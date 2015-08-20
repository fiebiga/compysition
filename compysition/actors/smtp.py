#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
# Created by Adam Fiebig
# Last modified: 5-5-2015 by Adam Fiebig
import gevent.monkey
gevent.monkey.patch_all(thread=False)
from compysition import Actor
from lxml import etree
from email.mime.text import MIMEText
import smtplib
import gsmtpd.server
import email
import dicttoxml
import traceback

class SMTPOut(Actor):
    '''**Module which sends mime emails with propertied specified in XML event data.**

    Parameters:

        - name (str):       The instance name.
    '''

    def __init__(self, name, address=None, key=None, host=("localhost", 25), *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.blockdiag_config["shape"] = "mail"
        self.logger.info("Initialized Notify Module")
        self.key = key or self.name
        self.host = host
        self.body_tag = 'Body'

    def consume(self, event, *args, **kwargs):
        msg_xml = etree.XML(event.data)
        to = msg_xml.find("To").text
        from_address = msg_xml.find("From").text
        if to != "None" and to is not None:
            msg = MIMEText(msg_xml.find(self.body_tag).text)    # Create a mime obj with our body text
            msg_xml.remove(msg_xml.find(self.body_tag))         # Remove the body tag so it's not set as a prop
            for element in msg_xml:                             # Set each tag's text as a property on the MIMEText obj
                msg[element.tag] = element.text

            self.send(msg, to, from_address)
            self.logger.info("Email notification sent to {0} from {1}".format(to, from_address), event=event)
        else:
            self.logger.info("No email recipient specified, notification was not sent", event=event)

        self.send_event(event)

    def send(self, msg, to, from_address):
        try:
            print "Sending to {0}".format(self.host)
            sender = smtplib.SMTP(self.host)
            sender.sendmail(from_address, to.split(","), msg.as_string(), )
            sender.quit()
        except Exception as err:
            print traceback.format_exc()

class SMTPIn(Actor):
    '''**Module which sends mime emails with propertied specified in XML event data.**

    Parameters:

        - name (str):       The instance name.
    '''

    def __init__(self, name, host="localhost", output='xml', *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.blockdiag_config["shape"] = "mail"
        self.output = output
        self.server = gsmtpd.server.SMTPServer(host)
        self.server.process_message = self.process_message
        self.server.logger = self.logger

    def pre_hook(self):
        self.server.start()

    def process_message(self, peer, mailfrom, rcpttos, data):
        headers = email.message_from_string(data)
        new_data = dict(zip(headers.keys(), headers.values()))
        new_data['payload'] = headers.get_payload()
        if self.output == 'xml':
            new_data = dicttoxml.dicttoxml(new_data, custom_root="email")

        self.send_event(self.create_event(data=new_data))


    def consume(self, event, *args, **kwargs):
        pass
