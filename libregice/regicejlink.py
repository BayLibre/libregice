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

from pylink import JLink
from libregice import RegiceClient

class RegiceJLink(RegiceClient):
    """
        A class derived from RegiceClient, to use OpenOCD

        This class provides a way to read and write memory using JTAG.
    """
    def __init__(self, args):
        self.jlink = JLink()
        self.jlink.open()
        if args.jlink_script:
            self.jlink.script_file(args.jlink_script)
        self.jlink.connect(args.jlink_device)

    def read(self, width, address):
        """
            Read the value of register

            :param width: The size, in bits, of the register
            :param address: The physical address of register to read
            :return: The value of register
        """
        return self.jlink.memory_read(address, 1, None, width)[0]

    def write(self, width, address, value):
        """
            Write a value to the register

            :param width: The size, in bits, of the register
            :param address: The physical address of register to write
            :param value: The value to write to the register
        """
        self.jlink.memory_write(address, [value], None, width)
