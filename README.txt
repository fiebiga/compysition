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

Full Circle WSGI Example
-------

For the example below, we want to execute an XML transformation on a request and send it back to the client in a fast
and concurrent way. All steps and executions are spun up as spawned greenlet on the router
    
.. image:: docs/examples/full_circle_wsgi_example.jpg
    :align: center
    
.. code-block:: python

	from compysition.router import Default
	from compysition.module import WSGI
	from compysition.module import BasicAuth
	from compysition.module import Transformer
	from compysition.module import Funnel
	
	from mymodules.module import SomeRequestExecutor
	
	router = Default()
	router.register(WSGIServer, "wsgi")
	router.register(BasicAuth, "auth")
	router.register(Funnel, "wsgi_collector")
	router.register(Transformer, "submit_transform", 'SourceOne/xsls/submit.xsl')
	router.register(Transformer, "acknowledge_transform", 'SourceOne/xsls/acknowledge.xsl', 'XML', 'submit_transform')  # *args are the subjects of transform
	router.register(SomeRequestExecutor, "request_executor")
	
	router.connect('wsgi.outbox', 'auth.inbox')
	router.connect('wsgi_collector.outbox', 'wsgi.inbox') # This collects messages from multiple sources and directs them to wsgi.inbox
	router.connect('auth.outbox', 'submit_transform.inbox')
	router.connect('auth.errors', 'wsgi_collector.auth_errors') # Redirect auth errors to the wsgi server as a 401 Unaothorized Error
	router.connect('submit_transform.outbox', 'request_executor.inbox')
	router.connect('submit_transform.errors', 'wsgi_collector.transformation_errors')
	router.connect('request_executor.outbox', 'acknowledge_transform.inbox')
	router.connect('acknowledge_transform.outbox', 'wsgi_collector.inbox')
	
	router.start()
	router.block()
	
Note how modular each component is. It allows us to configure any steps in between class method executions and add
any additional executions, authorizations, or transformations in between the request and response by simply
adding it into the message execution flow

One-way messaging example
-------

.. image:: docs/intro.png
    :align: center

.. code-block:: python

	from compysition.router import Default
	from compysition.module import TestEvent
	from compysition.module import RoundRobin
	from compysition.module import STDOUT

	router=Default()
	router.register(TestEvent, "input")
	router.register(RoundRobin, "mixing")
	router.register(STDOUT, "output1", prefix="I am number one: ")
	router.register(STDOUT, "output2", prefix="I am number two: ")
    
    	router.connect("input.outbox", "mixing.inbox")
    	router.connect("mixing.one", "output1.inbox")
    	router.connect("mixing.two", "output2.inbox")
    
    	router.start()
    	router.block()
    	
    	Output: 
    	I am number one: test
    	I am number two: test
    	I am number one: test
    	I am number two: test
    	I am number one: test
    	I am number two: test
    	I am number one: test
    	I am number two: test
    	I am number one: test
	I am number two: test


Installing
----------

Through Pypi:

	$ easy_install compysition

Or the latest development branch from Github:

	$ git clone git@github.com:fiebiga/compysition.git

	$ cd compysition

	$ sudo python setup.py install


Original Wishbone Project: Documentation
-------------

https://wishbone.readthedocs.org/en/latest/index.html


Other Available Modules <Original Wishbone Project>
-------

https://github.com/smetj/wishboneModules

Support
-------

You may email myself at fiebig.adam@gmail.com
