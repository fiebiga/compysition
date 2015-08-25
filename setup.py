#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  setup.py
#
#  Copyright 2014 Adam Fiebig <fiebig.adam@gmail.com>
#  Originally based on "wishbone" project by smetj
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
import re

PROJECT = 'compysition'
__version__ = re.search("__version__\s*=\s*'(.*)'", open('compysition/__init__.py').read(), re.M).group(1)
assert __version__

install_requires = ['gevent>=1.0',
                    'greenlet>=0.3.2',
                    'argparse==1.2.1',
                    'jsonschema==2.3.0',
                    'prettytable==0.7.2',
                    'python-daemon==1.6',
                    'pyyaml==3.11',
                    'msgpack-python==0.4.2',
                    'pyzmq==14.3.1',
                    'amqp==1.4.5',
                    'grequests==0.2.0',
                    'jinja2==2.7.3',
                    'jsonschema==2.3.0',
                    'gearman==2.0.2',
                    'pycrypto==2.6.1',
                    'configobj',
                    'restartlet',
                    'lxml',
                    'blockdiag',
                    'bottle',
                    'dicttoxml',
                    'gsmtpd']

try:
    long_description = open('README.rst', 'rt').read()
except IOError:
    long_description = ''

setup(
    name=PROJECT,
    version=__version__,

    description='Build event pipeline servers with minimal effort.',
    long_description=long_description,

    author='Adam Fiebig',
    author_email='fiebig.adam@gmail.com',

    url='https://github.com/fiebiga/compysition',
    download_url='https://github.com/fiebiga/compysition/tarball/master',

    classifiers=['Development Status :: 5 - Production/Stable',
                 'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3.3',
                 'Programming Language :: Python :: Implementation :: PyPy',
                 'Intended Audience :: Developers',
                 'Intended Audience :: System Administrators',
                 ],
    platforms=['Linux'],
    scripts=[],
    provides=[],
    install_requires=install_requires,
    namespace_packages=[],
    packages=find_packages(),
    package_data = {
        # If any package contains *.txt or *.rst files, include them:
        '': ['*.txt', '*.rst', '*.xml', '*.xsl', '*.conf'],
    },
    zip_safe=False,
    dependency_links=['https://github.com/surfly/gevent/tarball/master#egg=gevent-1.1'],
)
