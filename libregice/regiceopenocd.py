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

import threading
import time

from OpenOCD import OpenOCD
from libregice import RegiceClient, Watchpoint

class WatchpointOpenOCD(Watchpoint):
    """
        OpenOCD watchpoint

        This provides few methods to manage OpenOCD watchpoint.
        :param ocd: OpenOCD object
        :param address: The start address of the watchpoint
        :param length: The length of watchpoint, in bytes
        :param access: The type of access (R/W) that trigger the watchpoint
        :param callback: The callback to execute when watchpoint stops cpu
        :param data: The data to pass to callback
    """
    def __init__(self, ocd, address, length, access, callback, data):
        super(WatchpointOpenOCD, self).__init__(address, length, access,
                                                callback, data)
        write = None
        read = None
        read_write = None
        if access == Watchpoint.RW:
            read_write = True
        elif access == Watchpoint.READ:
            read = True
        elif access == Watchpoint.WRITE:
            write = True
        self.ocd = ocd
        self.watchpoint = self.ocd.WP(address, length, read, write, read_write)

    def enable(self):
        """
            Enable the watchpoint
        """
        self.ocd.Halt(1)
        self.watchpoint.Enable()
        self.ocd.Resume()

    def disable(self):
        """
            Disable the watchpoint
        """
        self.ocd.Halt(1)
        self.watchpoint.Disable()
        self.ocd.Resume()

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

class RegiceOpenOCDThread(threading.Thread):
    """
        Poll OpenOCD to get detect when the cpu stops because of a watchpoint
        or a breakpoint.
        :param ocd: OpenOCD object
        :param client: OpenOCD client
    """
    def __init__(self, ocd, client):
        super(RegiceOpenOCDThread, self).__init__()
        self.ocd = ocd
        self.client = client
        self.quit = False

    def run(self):
        """
            Poll the OpenOCD to detect when it stops

            Poll the OpenOCD to detect when it stops to run watchpoint or
            breakpoint callback.
            Because there is no way to detect which watchpoint has stopped the
            cpu, only one watchpoint is supported.

            This stops to poll when quit attribute is set to True.
        """
        while not self.quit:
            self.ocd.acquire()
            lines = self.ocd.Readout()
            self.ocd.release()
            if lines and self.client.watchpoint:
                pc_address = self.ocd.Reg('pc').Read()
                for address in self.client.watchpoints:
                    self.client.watchpoints[address].run(pc_address)
                self.ocd.Resume()
            else:
                time.sleep(0.001)

    def join(self, timeout=None):
        """
            Stop and join the thread
        """
        self.quit = True
        self.ocd.Resume()
        super(RegiceOpenOCDThread, self).join(timeout)

class RegiceOpenOCD(RegiceClient):
    """
        A class derived from RegiceClient, to use OpenOCD

        This class provides a way to read and write memory using JTAG.
    """
    def __init__(self):
        super(RegiceOpenOCD, self).__init__()
        self.ocd = OpenOCDThreadSafe()
        RegiceOpenOCDThread(self.ocd, self).start()

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

    def read_list(self, addresses):
        """
            Read the value of addresses listed in dict

            :param dict: A dictionnary with the width as key, and the list of
                         address to read for that width
            :return: a dictionnary of value read, and with the address used as
                     key
        """
        values = {}
        self.ocd.Halt(1)
        for width in addresses:
            ocd_read = getattr(self.ocd, 'ReadMem{}'.format(width))
            for address in addresses[width]:
                values[address] = ocd_read(address)
        self.ocd.Resume()
        return values

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

    def watchpoint(self, address, length, access, callback, data):
        """
            Add and enable a watchpoint

            This adds a watchpoint and enables it.
            When the cpu stop because of the watchpoint, this executes the
            callback.

            :param address: The start address of the watchpoint
            :param length: The length of watchpoint, in bytes
            :param access: The type of access (R/W) that trigger the watchpoint
            :param callback: The callback to execute when watchpoint stops cpu
            :param data: The data to pass to callback
        """
        if self.watchpoints:
            raise IndexError("No more than one watchpoint is supported")
        watchpoint = WatchpointOpenOCD(self.ocd, address, length, access,
                                       callback, data)
        self.watchpoints[address] = watchpoint
