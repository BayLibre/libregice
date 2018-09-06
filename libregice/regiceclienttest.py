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
from time import time, sleep

from configparser import ConfigParser
from libregice import RegiceClient
from libregice.device import Device

class RegisterSimulation:
    """
        A class to simulate register changes.

        RegiceClientTest doesn't set any fake register value,
        and the value of registers never change like it would happen on a real
        device executing a software.
        This provides some facilities to simulate a real platform.
        With the help of a sim file wich describes registers update to do,
        this create some register activity.
    """
    def __init__(self, client, svd):
        self.peripheral_name = ''
        self.section_iter = None
        self.section = None
        self.next_section = None
        self.config = ConfigParser()
        self.config.optionxform = lambda option: option
        self.device = Device(svd, client)
        self.time = 0

    def read(self, file):
        """
            Read a simulation file

            This reads a simulation and prepare its execution.
            :param file: A file pointer to a simulation file
        """
        self.config.read_string(file.read().decode())
        self.peripheral_name = self.config.get('Options', 'peripheral')
        self.config.remove_section('Options')

    def get_next_section(self):
        """
            Determine the next section to execute

            This find out which section should be executed next.
            Basically, section are executed in alphabetical order,
            but this could change using the 'goto' option.
            :return: The ssection to execute
        """
        if self.next_section:
            self.section = self.next_section
            self.section_iter = iter(self.config.sections())
            while next(self.section_iter) != self.next_section:
                continue
            self.next_section = None
        else:
            self.section = next(self.section_iter)
        return self.section

    def start(self):
        """
            Prepare and run the first section

            This load the first section and run it.
        """
        self.section_iter = iter(self.config.sections())
        self.update()

    def update(self):
        """
            Load the next section and run it

            This loads the next section and then runs it.
            This performs for each register or field write defined in simulation
            a write operations to register or field.
            If sleep option has been set, then this waita until time has
            expired.
            If goto option has been set, then this changes the next section to
            run.
        """
        if self.sleep():
            return

        section = self.get_next_section()
        for option in self.config.options(section):
            if option == 'goto':
                self.next_section = self.config.get(section, option)
                continue
            if option == 'sleep':
                timeout = self.config.get(section, option)
                self.sleep(int(timeout))
                continue
            if option == 'read':
                field_name = self.config.get(section, option)
                field = eval('self.device.{}.{}'.format(
                    self.peripheral_name, field_name))
                value = field.read()
                continue
            field = eval('self.device.{}.{}'.format(
                self.peripheral_name, option))
            value = self.config.get(section, option)
            field.write(int(value))

    def sleep(self, timeout=0):
        """
            Setup a timer a return True until it expire

            This is an async sleep function, which allow to wait without
            blocking.
            If the 'timeout' arguement is set to positive value, then this arms
            the timer. Until the the timer expires, it will return True.
            :param timeout: The timeout value. It must be a positive value to
                            enable the timer. Once the timer is enabled, this is
                            ignored.
            :return: True if the timer is enabled and has not expired, False
                     otherwise.
        """
        if self.time == 0 and timeout > 0:
            self.time = time() + timeout
        elif self.time == 0 and timeout == 0:
            return False
        elif self.time <= time():
            self.time = 0
            return False
        return True

class Simulation(threading.Thread):
    """
        A class to run a simulation
    """
    def __init__(self, client, svd, demo):
        super(Simulation, self).__init__()
        self.simu = RegisterSimulation(client, svd)
        self.simu.read(demo)
        self.quit = False

    def run(self):
        """
            Run the simulation

            This is started by start() method.
        """
        self.simu.start()
        while not self.quit:
            self.simu.update()
            if self.simu.sleep():
                sleep(0.1)

    def join(self, timeout=None):
        """
            Stop the simulation
        """
        self.quit = True
        super(Simulation, self).join(timeout)

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
        if not address in self.memory:
            self.memory[address] = 0
        return self.memory[address]

    def write(self, width, address, value):
        """
            Write a value to the register

            :param width: The size, in bits, of the register
            :param address: The physical address of register to write
            :param value: The value to write to the register
        """
        self.memory[address] = value
