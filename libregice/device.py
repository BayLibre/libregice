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
    DISABLED = 0
    READ = 1
    WRITE = 2

    def __init__(self, svd, client):
        self.__dict__['svd'] = svd
        self.__dict__['client'] = client
        self.__dict__['cached_value'] = None
        self.__dict__['cache_flags'] = self.DISABLED

    def __int__(self):
        return self.read()

    def __add__(self, other):
        return int(self) + int(other)

    def __sub__(self, other):
        return int(self) - int(other)

    def __mul__(self, other):
        return int(self) * int(other)

    def __truediv__(self, other):
        return int(self) / int(other)

    def __floordiv__(self, other):
        return int(self) // int(other)

    def __mod__(self, other):
        return int(self) % int(other)

    def __divmod__(self, other):
        return divmod(int(self), int(other))

    def __pow__(self, other):
        return pow(int(self), int(other))

    def __lshift__(self, other):
        return int(self) << int(other)

    def __rshift__(self, other):
        return int(self) >> int(other)

    def __and__(self, other):
        return int(self) & int(other)

    def __xor__(self, other):
        return int(self) ^ int(other)

    def __or__(self, other):
        return int(self) | int(other)

    def __radd__(self, other):
        return int(other) + int(self)

    def __rsub__(self, other):
        return int(other) - int(self)

    def __rmul__(self, other):
        return int(other) * int(self)

    def __rtruediv__(self, other):
        return int(other) / int(self)

    def __rmod__(self, other):
        return int(other) % int(self)

    def __rdivmod__(self, other):
        return divmod(int(other), int(self))

    def __rpow__(self, other):
        return pow(int(other), int(self))

    def __rlshift__(self, other):
        return int(other) << int(self)

    def __rrshift__(self, other):
        return int(other) >> int(self)

    def __rand__(self, other):
        return int(other) & int(self)

    def __rxor__(self, other):
        return int(other) ^ int(self)

    def __ror__(self, other):
        return int(other) | int(self)

    def __invert__(self):
        return ~int(self)

    def __lt__(self, other):
        return int(self) < int(other)

    def __le__(self, other):
        return int(self) <= int(other)

    def __eq__(self, other):
        return int(self) == int(other)

    def __ne__(self, other):
        return int(self) != int(other)

    def __ge__(self, other):
        return int(self) > int(other)

    def __gt__(self, other):
        return int(self) >= int(other)

    def __iadd__(self, other):
        self.write(int(self) + int(other))
        return self

    def __isub__(self, other):
        self.write(int(self) - int(other))
        return self

    def __imul__(self, other):
        self.write(int(self) * int(other))
        return self

    def __itruediv__(self, other):
        self.write(int(int(self) / int(other)))
        return self

    def __ifloordiv__(self, other):
        self.write(int(int(self) // int(other)))
        return self

    def __imod__(self, other):
        self.write(int(self) % int(other))
        return self

    def __iand__(self, other):
        self.write(int(self) & int(other))
        return self

    def __ior__(self, other):
        self.write(int(self) | int(other))
        return self

    def __ixor__(self, other):
        self.write(int(self) ^ int(other))
        return self

    def __ilshift__(self, other):
        self.write(int(self) >> int(other))
        return self

    def __irshift__(self, other):
        self.write(int(self) << int(other))
        return self

    def __ipow__(self, other):
        self.write(int(self) ** int(other))
        return self

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

    def read(self, force=False):
        """
            Read the value of field

            :param force: Bypass cache policy and read data from device
            :return: The value of field
        """
        value = self.parent.read(force)
        mask = (1 << self.bitWidth) - 1
        return (value >> self.bitOffset) & mask

    def write(self, value, force_read=False, force_write=False):
        """
            Write a value to field

            This write the value to field.

            :param value: The value to write
            :param force_read: Bypass cache policy and read data from device
            :param force_write: Bypass cache policy and write data to device
        """
        mask = ((1 << self.bitWidth) - 1) << self.bitOffset
        cached_value = self.parent.read(force_read) & ~mask
        self.parent.write(cached_value | (value << self.bitOffset), force_write)

    def __str__(self):
        return "{}.{}.{}".format(self.svd.parent.parent.name,
                                 self.svd.parent.name, self.name)

    def address(self):
        """
            Return the address of register

            This returns the absolute address of the register that owns this
            field.
            :return: the address of register
        """
        return self.parent.address()

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

    def read(self, force=False):
        """
            Read the value of register

            Read the value in the register, cache it and return it.
            If the cache is enabled for read, this returns the cached value.

            :param force: Bypass cache policy and read data from device
            :return: The value of register
        """
        if force or self.cached_value is None or \
            self.cache_flags & self.READ == 0:
            self.cached_value = self.client.read(self.svd.size,
                                                 self.svd.address())
        return self.cached_value

    def write(self, value, force=False):
        """
            Write a value to register

            This writes the value to register.
            if the cache is enabled for write, then the value will only be
            written to the cache.

            :param value: The value to write if not None
            :param force: Bypass cache policy and write data to device
        """
        self.cached_value = value
        if force or self.cache_flags & self.WRITE == 0:
            self.client.write(self.svd.size, self.svd.address(), value)

    def flush(self):
        """
            Flush the cache

            This forces to write cached value to register.
        """
        self.client.write(self.svd.size, self.svd.address(), self.cached_value)

    def __str__(self):
        return "{}.{}".format(self.svd.parent.name, self.name)

    def address(self):
        """
            Return the address of register

            :return: the address of register
        """
        return self.svd.address()

class RegicePeripheral:
    """
        A class derived from RegiceObject, to manipulate a peripheral
    """
    def __init__(self, svd, client):
        self.svd = svd
        self.client = client
        for register_name in svd.registers:
            register = svd.registers[register_name]
            register_obj = RegiceRegister(register, client)
            setattr(self, register_name, register_obj)

    def __getattr__(self, attr):
        return getattr(self.svd, attr)

    def cache_configure(self, flags):
        """
            Configure caching for peripheral's registers

            This configures caching for each registers in the peripheral.

            :param flags: cache flags, could be: RegiceObject.DISABLED,
                          RegiceObject.READ, RegiceObject.WRITE
        """
        for register_name in self.svd.registers:
            register = getattr(self, register_name)
            register.cache_flags = flags

    def cache_prefetch(self):
        """
            Prefetch the content of registers to cache

            This reads the value of each registers and updates the cache.
            This is useful to update all registers at once, and use the cached
            values to perform many read operations on registers without
            performance hit.
        """
        addresses = {}
        for register_name in self.svd.registers:
            register = self.svd.registers[register_name]
            if not register.size in addresses:
                addresses[register.size] = []
            addresses[register.size].append(register.address())
        values = self.client.read_list(addresses)

        for register_name in self.svd.registers:
            register = getattr(self, register_name)
            register.cached_value = values[register.address()]

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
