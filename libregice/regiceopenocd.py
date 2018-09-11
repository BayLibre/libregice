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

from OpenOCD import OpenOCD
from libregice import RegiceClient

class OpenOCDThreadSafe(OpenOCD):
    """
        A class derived from OpenOCD that is thread safe
    """
    def __init__(self, Host="localhost", Port=4444):
        self.lock = threading.Lock()
        self.blocking = False
        super(OpenOCDThreadSafe, self).__init__(Host, Port)

    def Readout(self):
        """
            Communication functions

            This works exactly like the original method except that
            if blocking attribute is False then the method will return None
            instead of waiting for data.

            In addition, because this accesses to a critical resource,
            a lock must be held before to call this method.
        """
        buf = ''
        out = []
        while True:
            if not self.blocking:
                data = self.tn.read_eager().decode()
                if data == '':
                    return None
                buf += data
            else:
                buf += self.tn.read_some().decode()
            lines = buf.splitlines()
            if len(lines) > 1:
                for buf in lines[:-1]:
                    if buf:
                        out.append(buf)
                buf = lines[-1]
            if buf == '> ':
                return out

    def Exec(self, Cmd, *args):
        """
            Execute a command

            This works exactly like the original method except that it will
            acquire a lock before to execute the command.
            This protects Readout method which access to a critical resource.
        """
        self.acquire()
        self.blocking = True
        line = super(OpenOCDThreadSafe, self).Exec(Cmd, *args)
        self.blocking = False
        self.release()
        return line

    def acquire(self):
        """
            Acquire a lock to protect Readout method
        """
        self.lock.acquire()

    def release(self):
        """
            Release the lock
        """
        self.lock.release()


class RegiceOpenOCD(RegiceClient):
    """
        A class derived from RegiceClient, to use OpenOCD

        This class provides a way to read and write memory using JTAG.
    """
    def __init__(self):
        self.ocd = OpenOCDThreadSafe()

    def read(self, width, address):
        """
            Read the value of register

            :param width: The size, in bits, of the register
            :param address: The physical address of register to read
            :return: The value of register
        """
        self.ocd.Halt(1)
        ocd_read = getattr(self.ocd, 'ReadMem{}'.format(width))
        value = ocd_read(address)
        self.ocd.Resume()
        return value

    def write(self, width, address, value):
        """
            Write a value to the register

            :param width: The size, in bits, of the register
            :param address: The physical address of register to write
            :param value: The value to write to the register
        """
        self.ocd.Halt(1)
        ocd_write = getattr(self.ocd, 'WriteMem{}'.format(width))
        value = ocd_write(address, value)
        self.ocd.Resume()
        return value
