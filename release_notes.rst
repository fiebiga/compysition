Compysition changelog
=====================

Version 1.0.55
~~~~~~~~~~~~~

- Modified behavior of a MajorDomo Broker so that it issues a disconnect command to a worker that heartbeats after it has been deleted from the broker. This then triggers a re-registration between the worker and broker.

Version 1.0.5
~~~~~~~~~~~~~

- Added MajorDomo implementation using ZeroMQ to public branch
	- Documentation on the structure of this design pattern is available here: http://rfc.zeromq.org/spec:7
	- Automatic registration of brokers and broadcasts of those brokers is accomplished dynamically with the RegistrationService
		- The requirements for a fully dynamic and successful design is as follows:
			- MDPClient, MDPBroker, MDPWorker, MDPRegistrationService


Version 1.0.1
~~~~~~~~~~~~~

- Completely refactored compysition to reflect rework done on wishbone
	- Refactoring was done while maintaining differences of compysition Actor model pattern, which include:
		- Support of N:1 producer to consumer queues (many actors can now use the reference of a single consuming queue). 
			Note that 1:N is inherently NOT feasible with this instance of the Actor model, and the N:1 producer to consumer queue is currently only defaulted to being allowed
			with the connected admin queues (logs, metrics, failed). This will be opened to all router.connect() calls in the next version
		- Support of M:N queues connected to ANY module. Queue creation is done automatically at the time "router.connect()" is called, rather than
			having to be done within the Actor module __init__ itself. Inboxes and Outboxes can be named anything, as defined in the "router.connect()" invocation
		- The default behavior is to invoke 'self.send_event(event)' on the Actor, which will send to ALL connect 'outbox' queues.

- Changed actors to pass references to queues, rather than use a router to route. (The "router" name will be changed to "manager" in the future to reflect it's new role')

- Changed default logging behavior
	- Timestamps are now generated at the time that the logger call is INVOKED, rather than when the log operation is performed
- Changed queue consumption behavior
	- Order of consumption is now guaranteed to consume in the order that the event is placed on the queue
- The compysition Queue is now a subclass of the gevent Queue. The compysition Queue simply provides a few key features, like "waitUntilContent" as a convenience method,
	and the generation of metrics (in/out rate) per queue

- Added concept of "error" queues. An expected error may not always be considered a 'failure' and may be routed differently in the logic of an application.
	These queues may be connect with the "connect_error" method on the router, and invoked with the "send_error" method within the actor.
	An example of this use case would be in the BasicAuth module - failing apache authentication would not be a module failure, but you would want to connect a queue to send the "401 Unauthorized"
	back to the apache integration module (e.g. wsgi). If an actual execution exception occurs, it may be appropriate to use the 'failed' queue.

- Each Actor now differentiates between "outbox", "inbox", and "error" queues, and keeps separate pools for them.

- Some convenience changes, and some changes to support a more pythonic approach:
	- Actors now are all passed *args and **kwargs
	- Consume is now all passed *args and **kwargs, including the origin queue
	- Metrics are not produced by default, it must be specified in Router creation to generate metrics or not. This is to prevent unnecessary overhead when metrics are not desired
		or configured to be viewable

Version 0.0.1
~~~~~~~~~~~~~

- Migration of naming from wishbone to compysition
- Addition of a wsgi module to allow for html based wsgi input
- Addition of a managedqueue module to allow for full cycle message transport
- Addition of several xml transformation elements
