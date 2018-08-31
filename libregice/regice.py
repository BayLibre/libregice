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

import os

from svd import SVD, SVDText
from regicecommon.pkg import open_resource

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

            Load a SVD file. If the file name is a valid path, the function will
            load the file. Otherwise, the function will try to get the SVD file
            from package. If the function can't find a SVD file, this raises a
            FileNotFoundError error.

            :param file: The name of the file to open to load the SVD
        """
        try:
            if os.path.exists(file):
                self.svd = SVD(file)
            else:
                self.svd = SVDText(open_resource(None, file).read())
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
