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

import sys
import unittest

from libregice import Regice, RegiceClient, RegiceClientTest
from libregice import SVDNotLoaded, InvalidRegister
from libregice.device import Device, RegiceRegister
from svd import SVD

class TestRegiceClientTest(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.client = RegiceClientTest()
        self.memory = self.client.memory

    def setUp(self):
        self.client.memory_restore()

    def test_read(self):
        address = list(self.memory.keys())[0]
        value = self.client.read(32, address)
        self.assertEqual(value, self.memory[address])

    def test_write(self):
        address = list(self.memory.keys())[0]
        value = 0x00001256
        self.client.write(32, address, value)
        self.assertEqual(value, self.memory[address])

class TestRegice(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.regice = Regice(RegiceClientTest())
        self.memory = self.regice.client.memory
        self.regice.load_svd('test.svd')

    def setUp(self):
        self.regice.client.memory_restore()

    def test_load(self):
        with self.assertRaises(FileNotFoundError):
            self.regice.load_svd('doesntexist.svd')

        self.regice.load_svd('test.svd')
        self.assertNotEqual(self.regice.svd, None)

    def test_get_peripheral_list(self):
        peripherals = self.regice.get_peripheral_list()
        self.assertEqual(len(peripherals), 2)
        self.assertIn('TEST1', peripherals)
        self.assertIn('TEST2', peripherals)

    def test_get_register_list(self):
        registers = self.regice.get_register_list('TEST1', None)
        self.assertEqual(len(registers), 2)
        self.assertIn('TESTA', registers)
        self.assertIn('TESTB', registers)

        registers = self.regice.get_register_list('TEST1', [])
        self.assertEqual(len(registers), 2)

        registers = self.regice.get_register_list('TEST1', ['TESTA'])
        self.assertEqual(len(registers), 1)
        self.assertIn('TESTA', registers)

        registers = self.regice.get_register_list('TEST1', ['TESTA', 'TESTB'])
        self.assertEqual(len(registers), 2)

    def test_read(self):
        expected = self.memory[0x00001234]
        value = self.regice.read('TEST1', 'TESTA')
        self.assertEqual(value, expected)

        with self.assertRaises(InvalidRegister):
            value = self.regice.read('TEST1', 'TESTC')

    def test_read_fields(self):
        fields = self.regice.read_fields('TEST1', 'TESTA')
        self.assertEqual(len(fields), 3)
        self.assertEqual(fields['A1'], 0)
        self.assertEqual(fields['A2'], 1)
        self.assertEqual(fields['A3'], 3)

        with self.assertRaises(InvalidRegister):
            fields = self.regice.read('TEST1', 'TESTC')

    def test_write_fields(self):
        fields = self.regice.read_fields('TEST1', 'TESTA')
        self.assertEqual(fields['A3'], 3)

        fields['A3'] = 4
        self.regice.write_fields('TEST1', 'TESTA', fields)

        fields = self.regice.read_fields('TEST1', 'TESTA')
        self.assertEqual(fields['A3'], 4)

    def test_write(self):
        value = 6
        self.regice.write('TEST1', 'TESTA', value)
        self.assertEqual(value, self.memory[0x00001234])

        with self.assertRaises(InvalidRegister):
            value = self.regice.write('TEST1', 'TESTC', value)

    def test_register_exist(self):
        self.assertTrue(self.regice.register_exist('TEST1', 'TESTA'))
        self.assertFalse(self.regice.register_exist('TEST1', 'TESTC'))

    def test_not_svd_loaded(self):
        svd = self.regice.svd
        self.regice.svd = None
        with self.assertRaises(SVDNotLoaded):
            self.regice.get_peripheral_list()
        with self.assertRaises(SVDNotLoaded):
            self.regice.read('TEST1', 'TESTA')
        self.regice.svd = svd

    def test_get_size(self):
        size = self.regice.get_size('TEST1', 'TESTA')
        self.assertEqual(size, 8)

    def test_get_address(self):
        address = self.regice.get_address('TEST1', 'TESTA')
        self.assertEqual(address, 0x00001234)
        address = self.regice.get_address('TEST1', 'TESTB')
        self.assertEqual(address, 0x00001238)

    def test_get_base_address(self):
        address = self.regice.get_base_address('TEST1')
        self.assertEqual(address, 0x00001234)

class TestRegiceObject(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        svd = SVD('test.svd')
        svd.parse()
        self.client = RegiceClientTest()
        self.dev = Device(svd, self.client)
        self.memory = self.client.memory

    def setUp(self):
        self.client.memory_restore()

    def test_peripheral(self):
        self.assertTrue(hasattr(self.dev, 'TEST1'))
        self.assertTrue(hasattr(self.dev, 'TEST2'))
        self.assertEqual(self.dev.TEST1.baseAddress, 0x00001234)

    def test_register(self):
        self.assertTrue(hasattr(self.dev.TEST1, 'TESTA'))
        self.assertTrue(hasattr(self.dev.TEST1, 'TESTB'))
        self.assertEqual(self.dev.TEST1.TESTA.addressOffset, 0)

    def test_field(self):
        self.assertTrue(hasattr(self.dev.TEST1.TESTA, 'A1'))
        self.assertTrue(hasattr(self.dev.TEST1.TESTA, 'A2'))

    def test_register_to_int(self):
        reg = self.dev.TEST1.TESTA
        address = reg.address()
        self.assertEqual(int(reg), self.memory[address])

    def test_register_write(self):
        reg = self.dev.TEST1.TESTA
        address = reg.address()

        reg.write(0)
        self.assertEqual(self.memory[address], 0)

        reg += 1
        reg.write()
        self.assertEqual(self.memory[address], 1)

    def test_register_numeric_op(self):
        reg = self.dev.TEST1.TESTA
        address = reg.address()
        self.assertEqual(reg + 1, self.memory[address] + 1)
        self.assertEqual(reg - 1, self.memory[address] - 1)
        self.assertEqual(reg * 2, self.memory[address] * 2)
        self.assertEqual(reg / 2, self.memory[address] / 2)
        self.assertEqual(reg // 2, self.memory[address] // 2)
        self.assertEqual(reg % 2, self.memory[address] % 2)
        self.assertEqual(divmod(reg, 2), divmod(self.memory[address], 2))
        self.assertEqual(reg ** 2, self.memory[address] ** 2)
        self.assertEqual(reg << 1, self.memory[address] << 1)
        self.assertEqual(reg >> 1, self.memory[address] >> 1)
        self.assertEqual(reg & 1, self.memory[address] & 1)
        self.assertEqual(reg ^ 1, self.memory[address] ^ 1)
        self.assertEqual(reg | 1, self.memory[address] | 1)

        self.assertEqual(1 + reg, 1 + self.memory[address])
        self.assertEqual(1 - reg, 1 - self.memory[address])
        self.assertEqual(2 * reg, 2 * self.memory[address])
        self.assertEqual(2 / reg, 2 / self.memory[address])
        self.assertEqual(2 % reg, 2 % self.memory[address])
        self.assertEqual(divmod(2, reg), divmod(2, self.memory[address]))
        self.assertEqual(2 ** reg, 2 ** self.memory[address])
        self.assertEqual(1 << reg, 1 << self.memory[address])
        self.assertEqual(1 >> reg, 1 >> self.memory[address])
        self.assertEqual(1 & reg, 1 & self.memory[address])
        self.assertEqual(1 ^ reg, 1 ^ self.memory[address])
        self.assertEqual(1 | reg, 1 | self.memory[address])

        self.assertEqual(not reg, not self.memory[address])
        self.assertEqual(1 < reg, 1 < self.memory[address])
        self.assertEqual(1 <= reg, 1 <= self.memory[address])
        self.assertEqual(1 > reg, 1 > self.memory[address])
        self.assertEqual(1 >= reg, 1 >= self.memory[address])
        self.assertEqual(1 == reg, 1 == self.memory[address])
        self.assertEqual(1 != reg, 1 != self.memory[address])
        self.assertEqual(~reg, ~self.memory[address])

        reg += 1
        self.assertTrue(hasattr(reg, 'cached_value'))
        reg -= 1
        self.assertTrue(hasattr(reg, 'cached_value'))
        reg *= 1
        self.assertTrue(hasattr(reg, 'cached_value'))
        reg /= 1
        self.assertTrue(hasattr(reg, 'cached_value'))
        reg //= 1
        self.assertTrue(hasattr(reg, 'cached_value'))
        reg %= 1
        self.assertTrue(hasattr(reg, 'cached_value'))
        reg &= 1
        self.assertTrue(hasattr(reg, 'cached_value'))
        reg |= 1
        self.assertTrue(hasattr(reg, 'cached_value'))
        reg ^= 1
        self.assertTrue(hasattr(reg, 'cached_value'))
        reg <<= 1
        self.assertTrue(hasattr(reg, 'cached_value'))
        reg >>= 1
        self.assertTrue(hasattr(reg, 'cached_value'))
        reg **= 1
        self.assertTrue(hasattr(reg, 'cached_value'))

    def test_field_read(self):
        print(int(self.dev.TEST1.TESTA.A1))
        self.assertTrue(self.dev.TEST1.TESTA.A1 == 0)
        self.assertTrue(self.dev.TEST1.TESTA.A2 == 1)
        self.assertTrue(self.dev.TEST1.TESTA.A3 == 3)

    def test_field_write(self):
        reg = self.dev.TEST1.TESTA
        address = reg.address()
        reg.A2.write(0)
        self.assertEqual(self.memory[address], 3)
        reg.A3.write(0)
        self.assertEqual(self.memory[address], 0)

def ext_get_freq(clk):
    return 1234

def ext_enable(clk):
    return clk.en_field.write(1)

def ext_disable(clk):
    return clk.en_field.write(0)

if __name__ == '__main__':
    unittest.main()
