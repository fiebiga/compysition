Compysition
<Based on the Wishbone Project>

========

What?
-----

The original project, Wishbone, is described as a Python application framework and CLI tool build and manage async event
pipeline servers with minimal effort.

We have created compysition to build off the simple way in which this project managed message flow across multiple
modules. Compysition also expands upon this module registration module to provide abstracted multi-process communication
via 0mq_, as well as the ability for full cyclical communication for in-process request/response behavior in a lightweight,
fast, and fully concurrent manner

.. _0mg: http://zeromq.org/

Example
-------

.. image:: docs/intro.png
    :align: center

.. code-block:: python

    >>> from compysition.router import Default
    >>> from compysition.module import TestEvent
    >>> from compysition.module import RoundRobin
    >>> from compysition.module import STDOUT
    >>>
    >>> router=Default()
    >>> router.register(TestEvent, "input")
    >>> router.register(RoundRobin, "mixing")
    >>> router.register(STDOUT, "output1", prefix="I am number one: ")
    >>> router.register(STDOUT, "output2", prefix="I am number two: ")
    >>>
    >>> router.connect("input.outbox", "mixing.inbox")
    >>> router.connect("mixing.one", "output1.inbox")
    >>> router.connect("mixing.two", "output2.inbox")
    >>>
    >>> router.start()
    >>> router.block()
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
