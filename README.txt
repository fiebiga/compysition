Compysition
========

What?
-----
::

	A Python application framework to build and manage async and highly concurrent event-driven data flow

I have created **compysition** to build off the simple way in which Wishbone_ managed message flow across multiple
actors. Compysition expands upon this module registration module to provide abstracted multi-process communication
via 0mq_, as well as the ability for full cyclical communication for in-process request/response behavior in a lightweight,
fast, and fully concurrent manner, using gevent_ greenlets and concurrency patterns to consume and output events

.. _0mq: http://zeromq.org/
.. _Wishbone: https://github.com/smetj/wishbone
.. _gevent: http://www.gevent.org

**Compysition is currently new and in pre-Beta release. It will be undergoing many deep changes in the coming months**
The **compysition** project is built upon the original work of the Wishbone_ project

Full Circle WSGI Example
-------

For the example below, we want to execute an XML transformation on a request and send it back to the client in a fast
and concurrent way. All steps and executions are spun up as spawned greenlet on the router
    
.. image:: docs/examples/full_circle_wsgi_example.jpg
    :align: center
    
.. code-block:: python

	from compysition import Director
	from compysition.actors import WSGI
	from compysition.actors import BasicAuth
	from compysition.actors import Transformer
	from compysition.actors import Funnel
	
	from myactors.module import SomeRequestExecutor
	
	director = Director()
	director.register(WSGIServer, "wsgi")
	director.register(BasicAuth, "auth")
	director.register(Funnel, "wsgi_collector")
	director.register(Transformer, "submit_transform", 'SourceOne/xsls/submit.xsl')
	director.register(Transformer, "acknowledge_transform", 'SourceOne/xsls/acknowledge.xsl', 'XML', 'submit_transform')  # *args are the subjects of transform
	director.register(SomeRequestExecutor, "request_executor")
	
	director.connect_queue('wsgi.outbox', 'auth.inbox')
	director.connect_queue('wsgi_collector.outbox', 'wsgi.inbox') # This collects messages from multiple sources and directs them to wsgi.inbox
	director.connect_queue('auth.outbox', 'submit_transform.inbox')
	director.connect_queue('auth.errors', 'wsgi_collector.auth_errors') # Redirect auth errors to the wsgi server as a 401 Unaothorized Error
	director.connect_queue('submit_transform.outbox', 'request_executor.inbox')
	director.connect_queue('submit_transform.errors', 'wsgi_collector.transformation_errors')
	director.connect_queue('request_executor.outbox', 'acknowledge_transform.inbox')
	director.connect_queue('acknowledge_transform.outbox', 'wsgi_collector.inbox')
	
	director.start()
	
	
Note how modular each component is. It allows us to configure any steps in between class method executions and add
any additional executions, authorizations, or transformations in between the request and response by simply
adding it into the message execution flow

One-way messaging example
-------

.. code-block:: python

	from compysition import Director
	from compysition.actors import TestEvent
	from compysition.actors import STDOUT

	director = Director()
	director.register(TestEvent, "event_generator", interval=1)
	director.register(STDOUT, "output_one", prefix="I am number one: ", timestamp=True)
	director.register(STDOUT, "output_two", prefix="I am number two: ", timestamp=True)
    
    director.connect_queue("event_generator.outbox_one_outbox", "output_one.inbox")
	director.connect_queue("event_generator.outbox_two_outbox", "output_two.inbox")
    
    director.start()
    
    	
	Output: 
	[2015-02-13 16:56:35.850659] I am number two: test
	[2015-02-13 16:56:35.850913] I am number one: test
	[2015-02-13 16:56:36.851588] I am number two: test
	[2015-02-13 16:56:36.851856] I am number one: test
	[2015-02-13 16:56:37.852456] I am number two: test
	[2015-02-13 16:56:37.852737] I am number one: test
	[2015-02-13 16:56:38.858107] I am number two: test
	[2015-02-13 16:56:38.858400] I am number one: test
	[2015-02-13 16:56:39.860292] I am number two: test
	[2015-02-13 16:56:39.860570] I am number one: test



Installing
----------

Through Pypi:

	$ easy_install compysition

Or the latest development branch from Github:

	$ git clone git@github.com:fiebiga/compysition.git

	$ cd compysition

	$ sudo python setup.py install


Support
-------

You may email myself at fiebig.adam@gmail.com
