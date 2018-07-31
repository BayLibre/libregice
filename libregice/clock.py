#!/usr/bin/env python
# -*- coding: utf-8 -*-

# MIT License
#
# Copyright (c) 2018 BayLibre
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

class InvalidDivider(Exception):
    """
        An exception raised when the divider could not be determined
    """
    pass

class InvalidFrequency(Exception):
    """
        An exception raised when the frequency is outside frequency range
    """
    pass

class UnknownClock(Exception):
    """
        An exception raised when the requested clock is not known
    """
    def __init__(self, clock):
        super().__init__("The clock {} doesn't exist".format(clock))

class MissingAttribute(Exception):
    """
        An exception raised when the clock has not been properly configured
    """
    def __init__(self, clock, attr):
        super().__init__("{}: The attribute {} has not been defined"
                         .format(clock, attr))

class MissingAttributes(Exception):
    """
        An exception raised when the clock has not been properly configured
    """
    def __init__(self, clock, attrs):
        super().__init__("{}: The attributes {} have not been defined"
                         .format(clock, attrs))

class ClockTree(object):
    """
        A class to represent the clock tree

        This class is used to register all clocks of a device.
        It provides many methods to manage the clocks or get their state.
    """
    def __init__(self):
        self.clocks = {}
        self.tree = {}

    def get(self, name):
        """
            Get a clock

            :param name: The name of the clock to get
            :return: A clock object, None if no clock name has bee provided,
                     or raise an UnknownClock exception if the clock doesn't
                     exist
        """
        if not name:
            return None
        if not name in self.clocks:
            raise UnknownClock(name)
        return self.clocks[name]

    def get_freq(self, name):
        """
            Get the clock frequency

            :param name: The name of the clock to get the frequency
            :return: The clock frequency, or 0 if the clock name is None
        """
        clock = self.get(name)
        if clock is None:
            return 0
        return clock.get_freq()

    def is_gated(self, name):
        """
            Return the state of the clock

            This returns the state of the clock, e.g. if the clock is gated
            or not. Basically, a clock is gated if, it is disabled or one
            of its ancestor is gated.

            :param name: The name of the clock to get the status
            :return: True if the clock is gated (disabled), False otherwise
        """
        clock = self.get(name)
        if clock is None:
            return True
        return self.get(name).enabled() is False

    def add(self, name, clock):
        """
            Add a clock to the tree

            :param name: The name of the clock to add
            :param clock: The clock to add
        """
        self.clocks[name] = clock

    def get_orphans(self):
        """
            Find all the clocks without parents

            This goes through all the clocks, and find those which don't have
            a parent. The goal is to find the root clocks, in order make a tree.

            :return: A list of clocks
        """
        orphans = {}
        for clock_name in self.clocks:
            clock = self.clocks[clock_name]
            if clock.parent or hasattr(clock, 'parents') and clock.parents:
                continue
            orphans[clock_name] = clock
        return orphans

    def get_children(self, parent):
        """
            Get the clock children

            This goes through the list of clocks to find all the children of
            the clock. This is used to construct the clock tree.

            :param parent: The name of the clock
            :return: A list of clocks
        """
        clocks = {}
        for clock_name in self.clocks:
            clock = self.clocks[clock_name]
            if clock.parent == parent:
                clocks[clock_name] = clock
            if hasattr(clock, 'parents') and parent in clock.parents.values():
                clocks[clock_name] = clock
        return clocks

    def build(self):
        """
            Build the clock tree

            This go through all the clocks, and check if they have been
            correctly configured. This allows to catch many errors at
            initialization, before to use the clock tree for debugging.

            :return: True if all tests passed, False otherwise
        """
        result = True
        for clock_name in self.clocks:
            clock = self.clocks[clock_name]
            if not clock.build():
                result = False
                continue
        return result

    def make_tree(self, parent=None, clocks=None):
        """
            Make and return the clock tree

            This creates a representation of the current clock tree.
            The result could be used to print a clock summary.

            :param parent: The parent clock, or None for the root clocks
            :param clocks: Children clocks, or None to start a tree from the scratch
            :return: a tree of clocks
        """
        if parent is None and clocks is None:
            orphans = self.get_orphans()
            self.tree = self.make_tree(None, orphans)
            return self.tree
        else:
            tree = {}
            for clock_name in clocks:
                clock = clocks[clock_name]
                if isinstance(clock, Mux):
                    mux_parent = clock.get_parent()
                    if mux_parent:
                        if not mux_parent == parent:
                            continue
                    else:
                        continue
                children = self.get_children(clock_name)
                tree[clock_name] = self.make_tree(clock, children)
            return tree

class Clock(object):
    """
        A class to represent a clock
    """
    def __init__(self, **kwargs):
        self.parent = kwargs.get('parent', None)
        self.name = kwargs.get('name', None)
        self.device = kwargs.get('device', None)
        self.en_field = kwargs.get('en_field', None)
        self.en_val = kwargs.get('en_val', 1)
        self.rdy_field = kwargs.get('rdy_field', None)
        self.rdy_val = kwargs.get('rdy_val', 1)

        if self.device:
            self.tree = self.device.clocktree
        else:
            self.tree = None

        if self.tree and self.name:
            self.tree.add(self.name, self)

    def _get_parent(self):
        return self.tree.get(self.parent)

    def get_parent(self):
        """
            Get the parent of the clock

            If the clock only have one parent, return it.
            If the clock has multiple parent (e.g. clock is a mux),
            then it calls _get_parent() method to get it.

            :return: The clock's parent
        """
        self.check()
        return self._get_parent()

    def _get_freq(self):
        raise InvalidFrequency()

    def get_freq(self):
        """
            Return the clock freq

            Each clock provide a method _get_freq() that calculates
            and returns the current frequency of the clock, based one
            parent's one.

            :return: The clock frequency, in Hz
        """
        self.check()
        return self._get_freq()

    def _enabled(self):
        if self.rdy_field:
            return self.rdy_field == self.rdy_val
        if self.en_field:
            return self.en_field == self.en_val
        return True

    def enabled(self):
        """
            Return True if the clock is enabled

            This get the state of the current clock, and state of all
            the ancestors. If one of the ancestor is not enabled then
            this clock is considered as disabled.

            :return: True if the clock and its ancestors are enabled
        """
        self.check()
        parent_enabled = True
        if self.parent:
            parent_enabled = self.get_parent().enabled()
        return self._enabled() & parent_enabled

    def _check(self):
        pass

    def check(self):
        """
            Raise an exception if something is not correctly configured

            This checks many variables and ensure that everything is
            configured to do the clock operations. This is used to catch
            error at one place and simplify the clock operations.
        """
        if not self.name:
            raise MissingAttribute(None, 'name')
        if not self.tree:
            raise MissingAttribute(self.tree, 'tree')
        self._check()

    def build(self):
        """
            Same as check(), but return False if something is wrong.

            :return: False if the clock is not correctly configure,
                     otherwise True
        """
        try:
            self._check()
        except Exception as ex:
            print(ex)
            return False
        return True

class FixedClock(Clock):
    """
        A class that represents a fixed clock
    """
    def __init__(self, **kwargs):
        super(FixedClock, self).__init__(**kwargs)
        self.freq = kwargs.get('freq', None)

    def _check(self):
        if self.freq is None:
            raise MissingAttribute(self.name, 'freq')

    def _get_freq(self):
        return self.freq

class Gate(Clock):
    """
        A class that represents a clock gate
    """
    def __init__(self, **kwargs):
        super(Gate, self).__init__(**kwargs)

    def _check(self):
        if not self.en_field:
            raise MissingAttribute(self.name, 'en_field')

    def _enabled(self):
        if self.rdy_field:
            return self.rdy_field == self.rdy_val
        return self.en_field == self.en_val

    def _get_freq(self):
        return self.get_parent().get_freq()

class PLL(Clock):
    """
        A class that represents a PLL clock
    """
    def __init__(self, **kwargs):
        super(PLL, self).__init__(**kwargs)
        self.ext_get_freq = kwargs.get('get_freq', None)

    def _get_freq(self):
        if hasattr(self, 'ext_get_freq') and self.ext_get_freq:
            return self.ext_get_freq(self)
        return 0

    def _check(self):
        if not hasattr(self, 'ext_get_freq') or not self.ext_get_freq:
            raise MissingAttribute(self.name, 'get_freq')

class Mux(Clock):
    """
        A class that represents a clock multiplexer
    """
    def __init__(self, **kwargs):
        super(Mux, self).__init__(**kwargs)
        self.mux_field = kwargs.get('mux_field', None)
        self.ext_get_mux = kwargs.get('get_mux', None)
        self.parents = kwargs.get('parents', {})

    def _check(self):
        if not self.parents:
            raise MissingAttribute(self.name, 'parents')
        if self.mux_field is None and self.ext_get_mux is None:
            raise MissingAttribute(self.name, ['mux_field', 'ext_get_mux'])
        if self.tree is None:
            raise MissingAttribute(self.name, 'tree')
        for parent_id in self.parents:
            parent = self.parents[parent_id]
            if parent is None:
                continue
            if not parent in self.tree.clocks:
                raise UnknownClock(parent)

    def _get_parent(self):
        if hasattr(self, 'ext_get_mux') and self.ext_get_mux:
            mux = self.ext_get_mux(self)
        else:
            mux = int(self.mux_field)
        parent_name = self.parents[mux]
        return self.tree.get(parent_name)

    def _get_freq(self):
        parent = self.get_parent()
        if parent is None:
            # There are valid case where parent could be none,
            # e.g no clock selected. Return 0 in that case.
            return 0
        return parent.get_freq()

    def _enabled(self):
        parent = self.get_parent()
        if parent is None:
            return False
        return True

class Divider(Clock):
    """
        A class that represents a Clock divider
    """
    ONE_BASED = 0
    POWER_OF_TWO = 1
    ZERO_TO_GATE = 2

    def __init__(self, **kwargs):
        super(Divider, self).__init__(**kwargs)
        self.div_table = kwargs.get('table', {})
        self.div = kwargs.get('div', None)
        self.div_field = kwargs.get('div_field', None)
        self.div_type = kwargs.get('div_type', self.ONE_BASED)
        self.ext_get_div = kwargs.get('get_div', None)

    def _check(self):
        if self.ext_get_div:
            return
        if self.div is None and self.div_field is None:
            raise MissingAttributes(self.name, ['div', 'div_field'])

    def _get_div(self):
        if self.ext_get_div:
            return self.ext_get_div(self)
        if self.div:
            return self.div
        if self.div_field:
            if self.div_table:
                div = int(self.div_field)
                if not div in self.div_table:
                    raise InvalidDivider()
                return self.div_table[div]
            if self.div_type == self.ONE_BASED:
                return int(self.div_field)
            if self.div_type == self.POWER_OF_TWO:
                return 1 << self.div_field
        raise InvalidDivider()

    def _get_freq(self):
        div = self._get_div()
        if div is None or (div == 0 and self.div_type == self.ZERO_TO_GATE):
            return 0
        return int(self.get_parent().get_freq() / div)

    def _enabled(self):
        div = self._get_div()
        if div is None or (div == 0 and self.div_type == self.ZERO_TO_GATE):
            return False
        return True
