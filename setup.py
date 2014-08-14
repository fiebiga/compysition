#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  setup.py
#
#  Copyright 2013 Jelle Smet <development@smetj.net>
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
#
#

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import sys

PROJECT = 'compysition'
VERSION = '0.0.4'
install_requires=['gevent>=1.0dev','argparse','greenlet>=0.3.2','jsonschema','prettytable','python-daemon',"pyyaml"]

try:
    long_description = open('README.rst', 'rt').read()
except IOError:
    long_description = ''

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

setup(
    name=PROJECT,
    version=VERSION,

    description='A Python application framework and CLI tool to build and manage async event pipeline servers with minimal effort, forked from the wishbone project',
    long_description=long_description,

    author='Adam Fiebig',
    author_email='fiebig.adam@gmail.com',

    url='https://github.com/fiebiga/compysition',
    download_url='https://github.com/fiebiga/compysition/tarball/master',

    classifiers=['Development Status :: 4 - Beta',
                 'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.6',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3.3',
                 'Programming Language :: Python :: Implementation :: PyPy',
                 'Intended Audience :: Developers',
                 'Intended Audience :: System Administrators',
                 ],
    extras_require={
        'testing': ['pytest'],
    },
    platforms=['Linux'],
    test_suite='compysition.test.test_compysition',
    cmdclass={'test': PyTest},
    scripts=[],

    provides=[],
    dependency_links=['https://github.com/surfly/gevent/tarball/master#egg=gevent-1.0dev'],
    install_requires=install_requires,
    namespace_packages=[],
    packages=find_packages(),
    zip_safe=False,
    entry_points={
        'console_scripts': ['compysition = compysition.bootstrap:main'],
        'compysition.builtin.flow': [
            'fanout = compysition.module.fanout:Fanout',
            'funnel = compysition.module.funnel:Funnel',
            'lockbuffer = compysition.module.lockbuffer:LockBuffer',
            'roundrobin = compysition.module.roundrobin:RoundRobin',
            'tippingbucket = compysition.module.tippingbucket:TippingBucket'
             ],
        'compysition.builtin.logging': [
            'humanlogformatter = compysition.module.humanlogformatter:HumanLogFormatter',
            'loglevelfilter = compysition.module.loglevelfilter:LogLevelFilter'
            ],
        'compysition.builtin.metrics': [
            'graphite = compysition.module.graphite:Graphite',
            ],
        'compysition.builtin.function': [
            'header = compysition.module.header:Header',
            ],
        'compysition.builtin.input': [
            'testevent = compysition.module.testevent:TestEvent'
            ],
        'compysition.builtin.output': [
            'null = compysition.module.null:Null',
            'stdout = compysition.module.stdout:STDOUT',
            'syslog = compysition.module.wbsyslog:Syslog',
            'slow = compysition.module.slow:Slow',
            ],
        'compysition.input': [
            ],
        'compysition.output': [
            ],
        'compysition.function': [
            ]
    }
)
