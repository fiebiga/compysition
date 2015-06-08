Compysition
========

What?
-----
::

	A Python application framework to build and manage asynchronous and highly concurrent event-driven data flow

I have created **compysition** to build off the simple way in which Wishbone_ managed message flow across multiple
modules. Compysition expands upon this module registration method to provide abstracted multi-process communication
via 0mq_, as well as the ability for full cyclical communication for in-process request/response behavior in a lightweight,
fast, and fully concurrent manner, using gevent_ greenlets and concurrency patterns to consume and output events

.. _0mq: http://zeromq.org/
.. _Wishbone: https://github.com/smetj/wishbone
.. _gevent: http://www.gevent.org

**Compysition is currently new and in pre-Beta release. It will be undergoing many deep changes in the coming months**
The **compysition** project is built upon the original work of the Wishbone_ project

Variations from the traditional Actor Model
-----

The traditional and strict actor model requires that all actors have exactly one inbox and one outbox. I found that this was
overly constraining for creating and crafting complex data flow models. So compysition inherently supports multiple inboxes
and multiple outboxes on every single actor.

To put it in actor model terms, every actor is also a "funnel" and a "fanout". 

The default behavior, unless stated otherwise in the module documentation, is that all modules will send/copy an event to ALL
connected outbox queues

Full Circle WSGI Example
-------

For the example below, we want to execute an XML transformation on a request and send it back to the client in a fast
and concurrent way. All steps and executions are spun up as spawned greenlet on the router
    
.. code-block:: python

	from compysition import Director
	from compysition.actors import WSGI, BasicAuth, Transformer
	
	from myproject.actors import SomeRequestExecutor
	from myprojectresources import my_xsl_files as xsls
	
	director = Director()
	wsgi 			= director.register_actor(WSGIServer, "wsgi")
	auth 			= director.register_actor(BasicAuth, "auth")
	submit_transform 	= director.register_actor(Transformer, "submit_transform", xsls['submit'])
	acknowledge_transform 	= director.register_actor(Transformer, "acknowledge_transform", my_xsl_files['acknowledge.xsl'])
	request_executor 	= director.register_actor(SomeRequestExecutor, "request_executor")
	
	director.connect_queue(wsgi, 			auth)
	director.connect_queue(auth, 			submit_transform)
	director.connect_queue_error(auth, 		wsgi) 			# Redirect auth errors to the wsgi server as a 401 Unaothorized Error
	director.connect_queue(submit_transform, 	request_executor)
	director.connect_queue_error(submit_transform, 	wsgi)
	director.connect_queue(request_executor, 	acknowledge_transform)
	director.connect_queue(acknowledge_transform, 	wsgi)
	
	director.start()
	
Note how modular each component is. It allows us to configure any steps in between class method executions and add
any additional executions, authorizations, or transformations in between the request and response by simply
adding it into the message execution flow

One-way messaging example
-------

.. code-block:: python

	from compysition import Director
	from compysition.actors import TestEvent, STDOUT

	director = Director()
	event_generator = director.register_actor(TestEvent, "event_generator", interval=1)
	output_one 	= director.register_actor(STDOUT, "output_one", prefix="I am number one: ", timestamp=True)
	output_two 	= director.register_actor(STDOUT, "output_two", prefix="I am number two: ", timestamp=True)
    
	director.connect_queue(event_generator, [output_one, output_two])
    
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

ZeroMQ MajorDomo Implementation Example
-------
The following example is a single-process example of the multi-process MajorDomo Protocal from ZMQ. The pieces noted 
could all be run outside this process in their own compysitionscript, scalable across multiple hosts and cores

.. code-block:: python

    from compysition.actors import MDPClient, MDPWorker, MDPBroker, WSGI, MDPBrokerRegistrationService, STDOUT, Data
    from compysition import Director

    director = Director()

    mdp_client          = director.register_actor(MDPClient,                     "mdp_client")
    mdp_broker          = director.register_actor(MDPBroker,                     "mdp_broker")     # This could be it's own process
    mdp_regservice      = director.register_actor(MDPBrokerRegistrationService,  "mdp_regservice") # This could be it's own process
    mdp_worker          = director.register_actor(MDPWorker,                     "mdp_worker", "test_service") # This (These) would be their own processes
    stdout              = director.register_actor(STDOUT,                        "stdout")
    data                = director.register_actor(Data,                          "data", data="Hello, this has been a test")

    wsgi                = director.register_actor(WSGI,                          "wsgi", run_server=True, address="0.0.0.0", port=7000)
    director.register_log_actor(STDOUT,                                          "stdoutmodule", timestamp=True)

    director.connect_queue(wsgi,             mdp_client)
    director.connect_queue(mdp_worker,       data)
    director.connect_queue(data,             mdp_worker)
    director.connect_queue(mdp_client,       wsgi)

    director.start()

After running this process, initiating a http request to http://127.0.0.1:7000/test_service would show the dataflow across MDP components

Installing
----------

Through Pypi:

	$ pip install compysition

Or the latest development branch from Github:

	$ git clone git@github.com:fiebiga/compysition.git
	$ cd compysition
	$ sudo python setup.py install

Support
-------

You may email myself at fiebig.adam@gmail.com
