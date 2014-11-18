Compysition
========

What?
-----

The **compysition** project is built upon the original work of the Wishbone_ project, which is described as follows:
::

	A Python application framework and CLI tool build and manage async event
	pipeline servers with minimal effort.


We have created **compysition** to build off the simple way in which Wishbone_ managed message flow across multiple
modules. Compysition also expands upon this module registration module to provide abstracted multi-process communication
via 0mq_, as well as the ability for full cyclical communication for in-process request/response behavior in a lightweight,
fast, and fully concurrent manner

.. _0mq: http://zeromq.org/
.. _Wishbone: https://github.com/smetj/wishbone

**Compysition is currently new and in pre-Beta release. It will be undergoing many deep changes in the coming months**


How?
-----

The **compysition* project uses a modified actor model combined with highly concurrent event-driven programming to achieve highly performant and scalable processes.

How does it differ from the traditional Actor model?
** Compysition modules (Actors) function as a N:M connector by default. Strict Actor model programming utilizes a 1:1 or N:1 or 1:N connection exclusively. This process makes sense academically, but from a development standpoint,
each data processing branch adds needless complexity when dealing with such strict limitations.

Full Circle WSGI Example
-------

For the example below, we want to execute an XML transformation on a request and send it back to the client in a fast
and concurrent way. All steps and executions are spun up as spawned greenlet on the router
    
.. code-block:: python

	#!/usr/bin/env python

	from compysition.router import Default
	from compysition.module import WSGI
	from compysition.module import BasicAuth
	from compysition.module import FileLogger
	from compysition.module import Transformer
	
	router = Default()

	router.registerModule(WSGI, "wsgi", run_server=True, address="127.0.0.1", port=7000, base_path="/my_base_path")
	router.registerModule(BasicAuth, "auth")
	router.registerModule(Transformer, "submit_transform", xslt_path='/my/xslt/submit.xsl')
	router.registerModule(Transformer, "acknowledge_transform", xslt_path='/my/xslt/acknowledge.xsl')

	# File Logging
	router.registerLogModule(FileLogger, "filelogger", "wsgi.log")

	# ServiceA
	router.connect('wsgi.serviceA', 'auth.inbox')
	router.connect('auth.outbox', 'submit_transform.inbox')
	router.connect_error('auth.error', 'wsgi.auth_error_inbox') 						# Redirect auth errors to the wsgi server as a 401 Unaothorized Error
	router.connect('submit_transform.outbox', 'acknowledge_transform.inbox')
	router.connect('acknowledge_transform.outbox', 'wsgi.acknowledge_transform_inbox')

	router.start()
	router.block()

Note how modular each component is. It allows us to configure any steps in between class method executions and add
any additional executions, authorizations, or transformations in between the request and response by simply
adding it into the message execution flow

One-way messaging example (Data Sink)
-------

.. image:: docs/intro.png
    :align: center

.. code-block:: python

	from compysition.router import Default
	from compysition.module import TestEvent
	from compysition.module import STDOUT

	router=Default()
	router.registerModule(TestEvent, "input")
	router.registerModule(STDOUT, "output_one", prefix="I am number one: ")
	router.registerModule(STDOUT, "output_two", prefix="I am number two: ")
    
	router.connectModule("input.output_one_outbox", "output_one.inbox")
	router.connectModule("input.output_two_outbox", "outbox_two.inbox")
    
	router.start()
	router.block()
    	
	Output: 
		1.0s:  	I am number one: test
		1.0s: 	I am number two: test
		2.0s:	I am number one: test
		2.0s:	I am number two: test
		3.0s:	I am number one: test
		3.0s:	I am number two: test
		4.0s:	I am number one: test
		4.0s:	I am number two: test
		5.0s:	I am number one: test
		5.0s:	I am number two: test

	* Note the 1:M inherently demonstrated here. This is different than a traditional Actor model, which would only support a 1:1 relationship, making the configuration of this simple use case overly difficult

Installing
----------

Through Pypi:

	$ easy_install compysition

Or the latest development branch from Github:

	$ git clone git@github.com:fiebiga/compysition.git

	$ cd compysition

	$ sudo python setup.py install
	
ZeroMQ MajorDomo Implementation
-------------------------------

TBD


Original Wishbone Project: Documentation
-------------

https://wishbone.readthedocs.org/en/latest/index.html


Other Available Modules <Original Wishbone Project>
-------

https://github.com/smetj/wishboneModules

Support
-------

You may email myself at fiebig.adam@gmail.com
