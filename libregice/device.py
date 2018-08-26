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

"""
    This module provides classes to manage device.

    Basically, this provides a class 'Device' that could be used as this,
    or it could be derived to implement some drivers (e.g clock).
    This relies on SVD to build a tree (peripherals, registers and fields).
    This uses the regice client to perform register accesses.
"""

class RegiceObject:
    """
        A class to easily manipulate a register or a field

        Each instance could represent a peripheral, a register or a field.
        This implements many operators, to read the value of register or field,
        or update them.
    """
    FORCE_READ = 1
    FORCE_WRITE = 2

    def __init__(self, svd, client):
        self.__dict__['svd'] = svd
        self.__dict__['client'] = client
        self.__dict__['cached_value'] = None
        self.__dict__['cache_flags'] = self.FORCE_READ

    def __int__(self):
        return self.read_cached()

    def __add__(self, other):
        return self.read_cached() + int(other)

    def __sub__(self, other):
        return self.read_cached() - int(other)

    def __mul__(self, other):
        return self.read_cached() * int(other)

    def __truediv__(self, other):
        return self.read_cached() / int(other)

    def __floordiv__(self, other):
        return self.read_cached() // int(other)

    def __mod__(self, other):
        return self.read_cached() % int(other)

    def __divmod__(self, other):
        return divmod(self.read_cached(), int(other))

    def __pow__(self, other):
        return pow(self.read_cached(), int(other))

    def __lshift__(self, other):
        return self.read_cached() << int(other)

    def __rshift__(self, other):
        return self.read_cached() >> int(other)

    def __and__(self, other):
        return self.read_cached() & int(other)

    def __xor__(self, other):
        return self.read_cached() ^ int(other)

    def __or__(self, other):
        return self.read_cached() | int(other)

    def __radd__(self, other):
        return int(other) + self.read_cached()

    def __rsub__(self, other):
        return int(other) - self.read_cached()

    def __rmul__(self, other):
        return int(other) * self.read_cached()

    def __rtruediv__(self, other):
        return int(other) / self.read_cached()

    def __rmod__(self, other):
        return int(other) % self.read_cached()

    def __rdivmod__(self, other):
        return divmod(int(other), self.read_cached())

    def __rpow__(self, other):
        return pow(int(other), self.read_cached())

    def __rlshift__(self, other):
        return int(other) << self.read_cached()

    def __rrshift__(self, other):
        return int(other) >> self.read_cached()

    def __rand__(self, other):
        return int(other) & self.read_cached()

    def __rxor__(self, other):
        return int(other) ^ self.read_cached()

    def __ror__(self, other):
        return int(other) | self.read_cached()

    def __invert__(self):
        return ~self.read_cached()

    def __lt__(self, other):
        return self.read_cached() < int(other)

    def __le__(self, other):
        return self.read_cached() <= int(other)

    def __eq__(self, other):
        return self.read_cached() == int(other)

    def __ne__(self, other):
        return self.read_cached() != int(other)

    def __ge__(self, other):
        return self.read_cached() > int(other)

    def __gt__(self, other):
        return self.read_cached() >= int(other)

    def _new_obj(self):
        return self.__class__(self.svd, self.client)

    def __iadd__(self, other):
        new_obj = self._new_obj()
        new_obj.write_cached(self.read_cached() + int(other))
        return new_obj

    def __isub__(self, other):
        new_obj = self._new_obj()
        new_obj.write_cached(self.read_cached() - int(other))
        return new_obj

    def __imul__(self, other):
        new_obj = self._new_obj()
        new_obj.write_cached(self.read_cached() * int(other))
        return new_obj

    def __itruediv__(self, other):
        new_obj = self._new_obj()
        new_obj.write_cached(int(self.read_cached() / int(other)))
        return new_obj

    def __ifloordiv__(self, other):
        new_obj = self._new_obj()
        new_obj.write_cached(int(self.read_cached() // int(other)))
        return new_obj

    def __imod__(self, other):
        new_obj = self._new_obj()
        new_obj.write_cached(self.read_cached() % int(other))
        return new_obj

    def __iand__(self, other):
        new_obj = self._new_obj()
        new_obj.write_cached(self.read_cached() & int(other))
        return new_obj

    def __ior__(self, other):
        new_obj = self._new_obj()
        new_obj.write_cached(self.read_cached() | int(other))
        return new_obj

    def __ixor__(self, other):
        new_obj = self._new_obj()
        new_obj.write_cached(self.read_cached() ^ int(other))
        return new_obj

    def __ilshift__(self, other):
        new_obj = self._new_obj()
        new_obj.write_cached(self.read_cached() >> int(other))
        return new_obj

    def __irshift__(self, other):
        new_obj = self._new_obj()
        new_obj.write_cached(self.read_cached() << int(other))
        return new_obj

    def __ipow__(self, other):
        new_obj = self._new_obj()
        new_obj.write_cached(self.read_cached() ** int(other))
        return new_obj

    def __getattr__(self, attr):
        return getattr(self.svd, attr)

class RegiceField(RegiceObject):
    """
        A class to easily manipulate a field

        Each instance could represent a field.
        This implements many operators, to read the value of fields,
        or update them.

    """
    def __init__(self, parent, svd, client):
        super(RegiceField, self).__init__(svd, client)
        self.parent = parent

    def read(self):
        """
            Read the value of field

            :return: The value of field
        """
        value = self.parent.read()
        mask = (1 << self.bitWidth) - 1
        return (value >> self.bitOffset) & mask

    def write(self, value):
        """
            Write a value to field

            This write the value to field.
            This forces a write to the register.

            :param value: The value to write
        """
        mask = ((1 << self.bitWidth) - 1) << self.bitOffset
        cached_value = self.parent.read_cached() & ~mask
        self.parent.write(cached_value | (value << self.bitOffset))

    def read_cached(self):
        """
            Read the cached value of field

            This returns the value cached by read().
            If there is no value in the cache, call read().

            :return: The value of field
        """
        value = self.parent.read_cached()
        mask = (1 << self.bitWidth) - 1
        return (value >> self.bitOffset) & mask

    def write_cached(self, value):
        """
            Write the field value to register cached value

            This updates the value of register cache with the value
            of the field.

            :param value: The value to write
        """
        cached_value = self.parent.read_cached()
        mask = (self.bitWidth << self.bitOffset)
        cached_value &= ~mask
        self.parent.write_cached(cached_value | (value << self.bitOffset))

    def __str__(self):
        return "{}.{}.{}".format(self.svd.parent.parent.name,
                                 self.svd.parent.name, self.name)

class RegiceRegister(RegiceObject):
    """
        A class to easily manipulate a register

        Each instance could represent a register.
        This implements many operators, to read the value of registers,
        or update them.
    """
    def __init__(self, svd, client):
        super(RegiceRegister, self).__init__(svd, client)
        for field_name in svd.fields:
            field = svd.fields[field_name]
            field_obj = RegiceField(self, field, client)
            setattr(self, field_name, field_obj)

    def read(self):
        """
            Read the value of register

            Read the value in the register, cache it and return it.
            :return: The value of register
        """
        self.cached_value = self.client.read(self.svd.size, self.svd.address())
        return self.cached_value

    def write(self, value=None):
        """
            Write a value to register

            This write the value (if one is given), or the value of cache to
            register.
            The cache is updated after the write operation.

            :param value: The value to write if not None
        """
        if value is None:
            value = self.cached_value
        self.client.write(self.svd.size, self.svd.address(), value)
        self.read()

    def read_cached(self):
        """
            Read the cached value of register

            This returns the value cached by read().
            If there is no value in the cache, call read().

            :return: The value of register
        """
        if not self.cached_value or self.cache_flags & self.FORCE_READ:
            self.read()
        return self.cached_value

    def write_cached(self, value):
        """
            Write a value to register cache

            This write the value to the register cache.

            :param value: The value to write
        """
        self.cached_value = value
        if self.cache_flags & self.FORCE_WRITE:
            self.write()

    def __str__(self):
        return "{}.{}".format(self.svd.parent.name, self.name)

class RegicePeripheral:
    """
        A class derived from RegiceObject, to manipulate a peripheral
    """
    def __init__(self, svd, client):
        self.svd = svd
        for register_name in svd.registers:
            register = svd.registers[register_name]
            register_obj = RegiceRegister(register, client)
            setattr(self, register_name, register_obj)

    def __getattr__(self, attr):
        return getattr(self.svd, attr)

class Device:
    """
        A class that represents a device

        Basically, this be used as this or it could be derived to implement
        some drivers (e.g clock).
        This provides some facilities to manipulate registers directly,
        or via drivers.
    """
    def __init__(self, svd, client):
#        self.drivers = {'clock': True}
        self.name = svd.name
        self.svd = svd
        self.client = client
        self.regice_init()
#        self.device_init()

    def device_init(self):
        """
            Initialize the device

            Try to load all the drivers.
            If a driver is not implemented, mark it as not available.
        """
        for driver in self.drivers:
            try:
                eval('self.{}_init()'.format(driver))
            except NotImplementedError:
                self.drivers[driver] = False

    def regice_init(self):
        """
            Initialize regice

            This populate the device with a tree of peripherals, registers and
            fields.
        """
        for peripheral_name in self.svd.peripherals:
            peripheral = self.svd.peripherals[peripheral_name]
            peripheral_obj = RegicePeripheral(peripheral, self.client)
            setattr(self, peripheral_name, peripheral_obj)
