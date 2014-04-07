#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  formatter.py
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
#
#

import time, re
import patterns

class Formatter(patterns.Singleton):
    xml_date = '%Y-%m-%d'

    def __getattr__(self, name):
        return getattr(self, 'default')

    def default(self, string, **kwargs):
        return string.strip()


class XML(Formatter):

    def zip(self, string=None, **kwargs):
        return string.rstrip('0')

    def date(self, string=None, **kwargs):
        if string.strip('0') == '': return '' # blank IBM i date
        from_format = kwargs.get('format', '%m%d%Y')
        stamp = time.strptime(string, from_format)
        return time.strftime(self.xml_date, stamp)

    def time(self, string=None, **kwargs):
        # yyyy-mm-dd-hh.mm.ss.xxxxxx
        return string

    def phone(self, string=None, **kwargs):
        if string.strip('0') == '': return ''
        return '({0}{1}{2}) {3}{4}{5}-{6}{7}{8}{9}'.format(*string) # assumes 10 digit. (All IBM i currently are)

    def numeric(self, string=None, **kwargs):
        #print '%s: XML.numric called (%s, %s)'% (self.__class__.__name__, string, kwargs)
        precision = int(kwargs.get('precision', 0))
        #print '%s: Precision has been set to %s)'% (self.__class__.__name__, precision)
        if precision is not 0: # if precision is given, 0 is different than ''.
            spec = '{{0:.{0}f}}'.format(precision) #dynamically create formating string base on precision
            #print '%s: Spec is "%s", precision "%s"'% (self.__class__.__name__, spec, precision)
            try:
                return spec.format(float(string) / (10 ** precision))
            except:
                return string.strip()
        else:
            #print '%s: Precision (%s) is 0'% (self.__class__.__name__, precision)
            return string.lstrip('0')


class FLS(Formatter):

    def default(self, string=None, **kwargs):
        return string.ljust(int(kwargs.get('length'))).upper()

    def zip(self, string='', **kwargs):
        return string.ljust(int(kwargs.get('length')), '0')

    def date(self, string=None, **kwargs):
        if string.strip('0') == '': return '0' * int(kwargs.get('length', 8)) # blank IBM i date
        to_format = kwargs.get('format', '%m%d%Y')
        stamp = time.strptime(string, self.xml_date)
        return time.strftime(to_format, stamp)

    def time(self, string=None, **kwargs):
        return string

    def phone(self, string='', **kwargs):
        if string.strip('0') == '': return '0' * int(kwargs.get('length', 10)) # blank IBM i phone
        return re.sub('\D', '', string)

    def numeric(self, string='', **kwargs):
        string = string.strip(' ')
        if string.strip('0') == '': return '0' * int(kwargs.get('length', 1))
        precision = int(kwargs.get('precision', 0))
        number = str(int(float(string) * (10 ** precision)))
        return number.zfill(int(kwargs.get('length')))