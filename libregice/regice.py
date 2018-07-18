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

from svd import SVD

class InvalidField(Exception):
    """
        An exception raised if the requested field doesn't exist

        :param register: The name of the register
        :param field: The name of the field that doesn't exist, and raised the
                      exception
    """
    def __init__(self, register, field):
        super().__init__("Invalid field " + register + "." + field)

class InvalidRegister(Exception):
    """
        An exception raised if the requested register doesn't exist

        :param register: The name of the register that doesn't exist,
                         and raised the exception
    """
    def __init__(self, peripheral, register):
        super().__init__("Invalid register " + peripheral + "." + register)

class InvalidPeripheral(Exception):
    """
        An exception raised if the requested peripheral doesn't exist

        :param peripheral: The name of the peripheral that doesn't exist,
                           and raised the exception
    """
    def __init__(self, peripheral):
        super().__init__("Invalid peripheral " + peripheral)

class SVDNotLoaded(Exception):
    """
        An exception raised if the SVD have not been loaded
    """
    def __init__(self):
        super().__init__("SVD file have not been loaded")

class RegiceClient:
    """
        A class to abstract access to memory and registers

        This is a base class that must be derived to provides
        to access to device memory and is registers.
    """
    def read(self, width, address):
        """
            Read the value of register

            :param width: The size, in bits, of the register
            :param address: The physical address of register to read
            :return: The value of register
        """
        raise NotImplementedError

    def write(self, width, address, value):
        """
            Write a value to the register

            :param width: The size, in bits, of the register
            :param address: The physical address of register to write
            :param value: The value to write to the register
        """
        raise NotImplementedError

class RegiceObject:
    """
        A class to easily manipulate a register or a field

        Each instance could represent a peripheral, a register or a field.
        This implements many operators, to read the value of register or field,
        or update them.
    """
    FORCE_READ = 1
    FORCE_WRITE = 2

    def __init__(self, svd, client, cache_flags):
        self.__dict__['svd'] = svd
        self.__dict__['client'] = client
        self.__dict__['cached_value'] = None
        self.__dict__['cache_flags'] = cache_flags

    def __int__(self):
        return self.read_cached()

    def __add__(self, other):
        return self.read_cached() + other

    def __sub__(self, other):
        return self.read_cached() - other

    def __mul__(self, other):
        return self.read_cached() * other

    def __truediv__(self, other):
        return self.read_cached() / other

    def __mod__(self, other):
        return self.read_cached() % other

    def __divmod__(self, other):
        return divmod(self.read_cached(), other)

    def __pow__(self, other):
        return pow(self.read_cached(), other)

    def __lshift__(self, other):
        return self.read_cached() << other

    def __rshift__(self, other):
        return self.read_cached() >> other

    def __and__(self, other):
        return self.read_cached() & other

    def __xor__(self, other):
        return self.read_cached() ^ other

    def __or__(self, other):
        return self.read_cached() | other

    def __radd__(self, other):
        return other + self.read_cached()

    def __rsub__(self, other):
        return other - self.read_cached()

    def __rmul__(self, other):
        return other * self.read_cached()

    def __rtruediv__(self, other):
        return other / self.read_cached()

    def __rmod__(self, other):
        return other % self.read_cached()

    def __rdivmod__(self, other):
        return divmod(other, self.read_cached())

    def __rpow__(self, other):
        return pow(other, self.read_cached())

    def __rlshift__(self, other):
        return other << self.read_cached()

    def __rrshift__(self, other):
        return other >> self.read_cached()

    def __rand__(self, other):
        return other & self.read_cached()

    def __rxor__(self, other):
        return other ^ self.read_cached()

    def __ror__(self, other):
        return other | self.read_cached()

    def __invert__(self):
        return ~self.read_cached()

    def __lt__(self, other):
        return self.read_cached() < other

    def __le__(self, other):
        return self.read_cached() <= other

    def __eq__(self, other):
        return self.read_cached() == other

    def __ne__(self, other):
        return self.read_cached() != other

    def __ge__(self, other):
        return self.read_cached() > other

    def __gt__(self, other):
        return self.read_cached() >= other

    def _new_obj(self):
        return self.__class__(self.svd, self.client, self.cache_flags)

    def __iadd__(self, other):
        new_obj = self._new_obj()
        new_obj.write_cached(self.read_cached() + other)
        return new_obj

    def __isub__(self, other):
        new_obj = self._new_obj()
        new_obj.write_cached(self.read_cached() - other)
        return new_obj

    def __imul__(self, other):
        new_obj = self._new_obj()
        new_obj.write_cached(self.read_cached() * other)
        return new_obj

    def __itruediv__(self, other):
        new_obj = self._new_obj()
        new_obj.write_cached(int(self.read_cached() / other))
        return new_obj

    def __imod__(self, other):
        new_obj = self._new_obj()
        new_obj.write_cached(self.read_cached() % other)
        return new_obj

    def __iand__(self, other):
        new_obj = self._new_obj()
        new_obj.write_cached(self.read_cached() & other)
        return new_obj

    def __ior__(self, other):
        new_obj = self._new_obj()
        new_obj.write_cached(self.read_cached() | other)
        return new_obj

    def __ixor__(self, other):
        new_obj = self._new_obj()
        new_obj.write_cached(self.read_cached() ^ other)
        return new_obj

    def __ilshift__(self, other):
        new_obj = self._new_obj()
        new_obj.write_cached(self.read_cached() >> other)
        return new_obj

    def __irshift__(self, other):
        new_obj = self._new_obj()
        new_obj.write_cached(self.read_cached() << other)
        return new_obj

    def __ipow__(self, other):
        new_obj = self._new_obj()
        new_obj.write_cached(self.read_cached() ** other)
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
    def __init__(self, parent, svd, client, cache_flags):
        super(RegiceField, self).__init__(svd, client, cache_flags)
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

class RegiceRegister(RegiceObject):
    """
        A class to easily manipulate a register

        Each instance could represent a register.
        This implements many operators, to read the value of registers,
        or update them.
    """
    def __init__(self, svd, client, cache_flags):
        super(RegiceRegister, self).__init__(svd, client, cache_flags)
        for field_name in svd.fields:
            field = svd.fields[field_name]
            field_obj = RegiceField(self, field, client, cache_flags)
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

class RegicePeripheral:
    """
        A class derived from RegiceObject, to manipulate a peripheral
    """
    def __init__(self, svd, client, cache_flags):
        self.svd = svd
        for register_name in svd.registers:
            register = svd.registers[register_name]
            register_obj = RegiceRegister(register, client, cache_flags)
            setattr(self, register_name, register_obj)

    def __getattr__(self, attr):
        return getattr(self.svd, attr)

class RegiceDevice:
    """
        A class derived from RegiceObject, which is used as root of all other
        objects
    """
    def __init__(self, svd, client, cache_flags=0):
        for peripheral_name in svd.peripherals:
            peripheral = svd.peripherals[peripheral_name]
            peripheral_obj = RegicePeripheral(peripheral, client, cache_flags)
            setattr(self, peripheral_name, peripheral_obj)

class Regice:
    """
        A class to manipulate memory, registers remotely

        This provides some methods to read / write memory and registers,
        remotely (e.g. JTAG).
        JTAG is not mandatory, but this is the recommanded way to access
        to the remote device because this is the less intrusive.

        This uses a SVD file to get peripherals, registers, and fields name,
        address and many other properties.
        This provides a more easy and generic way to do read / write operations.

        :param client: The client that connects to device, and provides
                       methods to access to device memory and register
    """
    def __init__(self, client):
        self.svd = None
        self.peripheral = None
        self.client = client

    def load_svd(self, file):
        """
            Load the SVD file

            :param file: The name of the file to open to load the SVD
        """
        try:
            self.svd = SVD(file)
            self.svd.parse()
        except OSError:
            raise FileNotFoundError

    def svd_get(self):
        """
            Get the svd. If it have not been loaded, it raise an exception.

            :return: The svd, or raise SVDNotLoaded exception
        """
        if self.svd is None:
            raise SVDNotLoaded()
        return self.svd

    def svd_get_peripheral_list(self):
        """
            Get a list of peripherals

            :return: A list of peripherals
        """
        svd = self.svd_get()
        return svd.peripherals.keys()

    def svd_get_peripheral(self, peripheral):
        """
            Get a peripheral

            :return: The name of peripheral, or raise an InvalidPeripheral
                     exception if the peripheral doesn't exist
        """
        svd = self.svd_get()
        if not peripheral in self.svd_get_peripheral_list():
            raise InvalidPeripheral(peripheral)
        return svd.peripherals[peripheral]

    def svd_get_register_list(self, svd, peripheral):
        """
            Get a list of registers present in peripheral

            :param svd: A peripheral object, obtained from a previous request.
                        If none, fallback to peripheral name.
            :param peripheral: The name of peripheral we want to get the
                               registers

            :return: A list of registers
        """
        if svd is None:
            svd = self.svd_get_peripheral(peripheral)
        return svd.registers.keys()

    def svd_get_register(self, svd, peripheral, register):
        """
            Get a peripheral register

            :param svd: A peripheral object, obtained from a previous request.
                        If none, fallback to peripheral name.
            :param peripheral: The name of peripheral we want to get the
                               registers
            :param register: The name of register to get
            :return: The requested register, or raise an InvalidRegister
                     exception if the register doesn't exist
        """
        if svd is None:
            svd = self.svd_get_peripheral(peripheral)
        if not register in svd.registers:
            raise InvalidRegister(svd.name, register)
        return svd.registers[register]

    def svd_get_field_list(self, svd, peripheral, register):
        """
            Get a list of register fields

            :param svd: A register object, obtained from a previous request.
                        If none, fallback to register name.
            :param peripheral: The name of peripheral
            :param register: The name of register we want to get the fields
            :return: A list of fields
        """
        if svd is None:
            svd = self.svd_get_register(None, peripheral, register)
        return svd.fields.keys()

    def svd_get_field(self, svd, peripheral, register, field):
        """
            Get a register field

            :param svd: A register object, obtained from a previous request.
                        If none, fallback to register name.
            :param peripheral: The name of peripheral
            :param register: The name of register we want to get the fields
            :param field: The name of the field to get
            :return: The requested field, or raise an InvalidField exception
                     if the field doesn't exist
        """
        if svd is None:
            svd = self.svd_get_register(None, peripheral, register)
        if not field in svd.fields:
            raise InvalidField(register, field)
        return svd.fields[field]

    def get_peripheral_list(self):
        return self.svd_get_peripheral_list()

    def get_register_list(self, peripheral, registers_name):
        """
            Get a list of peripheral registers

            This returns a list of registers from peripheral.
            This could be used to get one, few or all registers,
            depending on the value of registers_name.

            :param peripheral: The name of peripheral we want to get the
                               registers
            :param registers_name: A list of register name to get
            :return: A list of peripheral name
        """
        register_list = self.svd_get_register_list(None, peripheral)
        if registers_name is None or registers_name == []:
            return register_list

        registers = []
        for register in registers_name:
            if not register in register_list:
                raise InvalidRegister(peripheral, register)
            registers.append(register)

        return registers

    def peripheral_exist(self, peripheral):
        """
            Check if the peripheral exists

            :param peripheral: The name of peripheral to test
            :return: True the peripheral exists, False if it doesn't
        """
        try:
            self.svd_get_peripheral(peripheral)
        except InvalidPeripheral:
            return False
        return True

    def register_exist(self, peripheral, register):
        """
            Check if a register exists in peripheral

            :param peripheral: The name of peripheral
            :param register: The name of register to test
            :return: True the register exists, False if it doesn't
        """
        try:
            self.svd_get_register(None, peripheral, register)
        except InvalidRegister:
            return False
        return True

    def field_exist(self, peripheral, register, field):
        """
            Check if a field exists in register

            :param peripheral: The name of peripheral
            :param register: The name of register
            :param field: The name of the field to get
            :return: True the field exists, False if it doesn't
        """
        try:
            self.svd_get_field(None, peripheral, register, field)
        except InvalidField:
            return False
        return True

    def get_address(self, peripheral, register):
        """
            Return the physical address of register

            :param peripheral: The name of peripheral
            :param register: The name of register
            :return: The physical address
        """
        register = self.svd_get_register(None, peripheral, register)
        return register.address()

    def get_base_address(self, peripheral):
        """
            Return the base address of peripheral

            :param peripheral: The name of peripheral
            :return: The physical address
        """
        return self.svd_get_peripheral(peripheral).baseAddress

    def get_size(self, peripheral, register):
        """
            Get the register size

            :param peripheral: The name of peripheral
            :param register: The name of register
            :return: The size of register, in bytes
        """
        register = self.svd_get_register(None, peripheral, register)
        return int(register.size / 4)

    def read(self, peripheral, register):
        """
            Read the register

            :param peripheral: The name of peripheral
            :param register: The name of register
            :return: The value of register
        """
        register = self.svd_get_register(None, peripheral, register)
        return self.client.read(register.size, register.address())

    def write(self, peripheral, register, value):
        """
            Write a value to register

            :param peripheral: The name of peripheral
            :param register: The name of register
            :param value: The value to write
        """
        register = self.svd_get_register(None, peripheral, register)
        return self.client.write(register.size, register.address(), value)

    def read_fields(self, peripheral, register):
        """
            Read the register and return fields value

            :param peripheral: The name of peripheral
            :param register: The name of register
            :return: A dict of fields
        """
        value = self.read(peripheral, register)
        register = self.svd_get_register(None, peripheral, register)
        fields = register.fields

        fields_list = {}
        for field in fields:
            mask = (1 << fields[field].bitWidth) - 1
            fields_list[field] = (value >> fields[field].bitOffset) & mask

        return fields_list

    def write_fields(self, peripheral, register, fields):
        """
            Write one or more fields to register

            :param peripheral: The name of peripheral
            :param register: The name of register
            :param fields: A dict of fields
        """
        value = 0
        register = self.svd_get_register(None, peripheral, register)
        svd_fields = register.fields

        for field in fields:
            value |= (int(fields[field]) << svd_fields[field].bitOffset)
        return self.client.write(register.size, register.address(), value)
