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

from libregice import RegiceClient

class RegiceClientTest(RegiceClient):
    """
        A class derived from RegiceClient, made for testing

        This class implements some methods required to test Regice.
        This provides a fake memory, that could be used to simulate read
        and write.
    """
    def __init__(self):
        self.memory_save = {
            0x00001234: 0x00100003,
            0x00001238: 0x00010000,
            0x0000123c: 0x80000000,
        }
        self.memory = {}
        self.memory_restore()

    def memory_restore(self):
        """
            Restore the memory to its default state

            Tests can alterate the the fake memory. This restores the
            memory to its original state, and garanty that whatever are
            the tests order, they will always success.
        """
        for addr in self.memory_save:
            self.memory[addr] = self.memory_save[addr]

    def read(self, width, address):
        """
            Read the value of register

            :param width: The size, in bits, of the register
            :param address: The physical address of register to read
            :return: The value of register
        """
        return self.memory[address]

    def write(self, width, address, value):
        """
            Write a value to the register

            :param width: The size, in bits, of the register
            :param address: The physical address of register to write
            :param value: The value to write to the register
        """
        self.memory[address] = value
