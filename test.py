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

from libregice import Regice, RegiceClient, SVDNotLoaded, InvalidRegister
from libregice import RegiceClientTest, RegiceDevice, RegiceRegister
from libregice.clock import FixedClock, Clock, Gate, Mux, ClockTree
from libregice.clock import Divider, PLL
from libregice.clock import InvalidDivider, UnknownClock, InvalidFrequency
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
        self.dev = RegiceDevice(svd, self.client, RegiceRegister.FORCE_READ)
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

class ClockTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        svd = SVD('test.svd')
        svd.parse()
        self.client = RegiceClientTest()
        self.dev = RegiceDevice(svd, self.client)
        self.memory = self.client.memory

    @classmethod
    def setUp(self):
        self.client.memory_restore()

class TestClock(ClockTestCase):
    def test_clock_add_to_tree(self):
        tree = ClockTree()
        self.assertEqual(tree.clocks, {})

        Clock(device=self.dev)
        self.assertEqual(tree.clocks, {})

        Clock(name='test1')
        self.assertEqual(tree.clocks, {})

        Clock(device=self.dev, name='test1')
        self.assertIn('test1', self.dev.clocktree.clocks)

    def test_check(self):
        clk = Clock(name='test1')
        with self.assertRaises(Exception):
            clk.check()

        clk = Clock(device=self.dev)
        with self.assertRaises(Exception):
            clk.check()

        clk = Clock(device=self.dev, name='test1')
        clk.check()

    def test_get_parent(self):
        clk1 = Clock(device=self.dev, name='test1')
        self.assertEqual(clk1.get_parent(), None)

        clk2 = Clock(device=self.dev, name='test2', parent='test1')
        self.assertEqual(clk2.get_parent(), clk1)

    def test_get_freq(self):
        clk = Clock(device=self.dev, name='test1')
        with self.assertRaises(InvalidFrequency):
            clk.get_freq()

class TestGate(ClockTestCase):
    def test_enabled(self):
        field = self.dev.TEST1.TESTA.A1
        clock = Gate(name='gate', device=self.dev, en_field=field)
        self.dev.TEST1.TESTA.A1.write(1)
        self.assertTrue(clock.enabled())
        self.dev.TEST1.TESTA.A1.write(0)
        self.assertFalse(clock.enabled())

        clock = Gate(name='gate', device=self.dev,
                     en_field=field, rdy_field=field)
        self.dev.TEST1.TESTA.A1.write(0)
        self.assertFalse(clock.enabled())

    def test_build(self):
        clock = Gate(device=self.dev)
        self.assertFalse(clock.build())
        clock = Gate(device=self.dev, en_field=self.dev.TEST1.TESTA.A1)
        self.assertTrue(clock.build())

class TestFixedClock(ClockTestCase):
    def test_fixed_clock(self):
        clock = FixedClock(freq=123456)
        self.assertEqual(clock.freq, 123456)

    def test_get_freq(self):
        clock = FixedClock(name='osc', device=self.dev, freq=123456)
        self.assertEqual(clock.get_freq(), 123456)

    def test_build(self):
        clock = FixedClock()
        self.assertFalse(clock.build())

        clock = FixedClock(freq=123456)
        self.assertTrue(clock.build())

def ext_get_mux(self):
    return 0

class TestMux(ClockTestCase):
    @classmethod
    def setUpClass(self):
        super(TestMux, self).setUpClass()
        self.mux_field = self.dev.TEST1.TESTA.A3
        self.tree = ClockTree()
        FixedClock(name='test0', device=self.dev, freq=1234)
        FixedClock(name='test1', device=self.dev, freq=123456)
        FixedClock(name='test3', device=self.dev, freq=12345)
        self.mux_parents = {0: 'test0', 1: 'test1', 3: 'test3'}
        self.mux = Mux(name='muxe', device=self.dev,
                       parents=self.mux_parents, mux_field=self.mux_field)

    def test_get_parent(self):
        parent = self.mux.get_parent()
        self.assertEqual(parent.name, 'test3')

        mux = Mux(name='mux', device=self.dev, parents=self.mux_parents,
                  get_mux=ext_get_mux)
        parent = mux.get_parent()
        self.assertEqual(parent.name, 'test0')

    def test_get_freq(self):
        self.assertEqual(self.mux._get_freq(), 12345)

        mux = Mux(name='pll', device=self.dev,
                  parents={0: 'test0', 1: 'test1', 3: None},
                  mux_field=self.dev.TEST1.TESTA.A3)
        self.assertEqual(mux.get_freq(), 0)

    def test_build(self):
        mux = Mux()
        self.assertFalse(mux.build())

        mux = Mux(parents={0: 'parent1', 1: 'parent2'})
        self.assertFalse(mux.build())

        mux = Mux(parents={0: 'parent1', 1: 'parent2'},
                  mux_field=self.dev.TEST1.TESTA.A3)
        self.assertFalse(mux.build())

        mux = Mux(device=self.dev, parents={0: 'test0', 1: 'test4'},
                  mux_field=self.dev.TEST1.TESTA.A3)
        self.assertFalse(mux.build())

        mux = Mux(device=self.dev, parents={0: 'test0', 1: 'test1'},
                  mux_field=self.dev.TEST1.TESTA.A3)
        self.assertTrue(mux.build())

        mux = Mux(device=self.dev, parents={0: 'test0', 1: 'test1', 2: None},
                  mux_field=self.dev.TEST1.TESTA.A3)
        self.assertTrue(mux.build())

    def test_enabled(self):
        mux = Mux(name='pll', device=self.dev, parents={0: 'test0', 3: None},
                  mux_field=self.dev.TEST1.TESTA.A3)
        self.assertFalse(mux.enabled())
        self.dev.TEST1.TESTA.A3.write(0)
        self.assertTrue(mux.enabled())
        self.dev.TEST1.TESTA.A3.write(3)

def ext_get_div(div):
    return 3

def ext_get_div_none(div):
    return None

def ext_get_div_zero(div):
    return 0

class TestDivider(ClockTestCase):
    def test_build(self):
        div = Divider()
        self.assertFalse(div.build())

        div = Divider(parent='test')
        self.assertFalse(div.build())

        div = Divider(parent='test', div=2)
        self.assertTrue(div.build())

        table = {0: 1, 1: 4, 2: 16}
        div = Divider(parent='test', table=table)
        self.assertFalse(div.build())

        div = Divider(parent='test', table=table,
                      div_field=self.dev.TEST1.TESTA.A3)
        self.assertTrue(div.build())

        div = Divider(parent='test', table=table)
        self.assertFalse(div.build())

        div = Divider(parent='test', div_field=self.dev.TEST1.TESTA.A3)
        self.assertTrue(div.build())

    def test_get_div(self):
        tree = ClockTree()
        FixedClock(name='test', device=self.dev, freq=123456)

        div = Divider(name='div', device=self.dev, parent='test', div=2)
        self.assertEqual(div._get_div(), 2)

        div = Divider(name='div', device=self.dev, parent='test',
                      div_field=self.dev.TEST1.TESTA.A3)
        self.assertEqual(int(div._get_div()), 3)

        div = Divider(name='div', device=self.dev, parent='test',
                      div_field=self.dev.TEST1.TESTA.A3,
                      div_type=Divider.POWER_OF_TWO)
        self.assertEqual(int(div._get_div()), 8)

        div = Divider(name='div', device=self.dev, parent='test',
                      div_field=self.dev.TEST1.TESTA.A3, table={3: 12, 4: 16})
        self.assertEqual(int(div._get_div()), 12)

        self.dev.TEST1.TESTA.A3.write(2)
        with self.assertRaises(InvalidDivider):
            div._get_div()

        div = Divider(name='div', device=self.dev, parent='test',
                      div_field=self.dev.TEST1.TESTA.A3, div_type=9999)
        with self.assertRaises(InvalidDivider):
            div._get_div()

        div = Divider(name='div', device=self.dev, parent='test',
                      get_div=ext_get_div)
        self.assertTrue(div.build())
        self.assertEqual(int(div._get_div()), 3)

    def test_get_freq(self):
        freq=123456
        tree = ClockTree()
        FixedClock(name='test', device=self.dev, freq=freq)

        div = Divider(name='div', device=self.dev, parent='test', div=2)
        self.assertEqual(div._get_freq(), freq / 2)

        div = Divider(name='div', device=self.dev, parent='test',
                      get_div=ext_get_div_none)
        self.assertEqual(div._get_freq(), 0)

        div = Divider(name='div', device=self.dev, parent='test',
                      get_div=ext_get_div_zero)
        with self.assertRaises(ZeroDivisionError):
            self.assertEqual(div._get_freq(), 0)

        div = Divider(name='div', device=self.dev, parent='test',
                      get_div=ext_get_div_zero, div_type=Divider.ZERO_TO_GATE)
        self.assertEqual(div._get_freq(), 0)

    def test_enabled(self):
        freq=123456
        tree = ClockTree()
        FixedClock(name='test', device=self.dev, freq=freq)

        div = Divider(name='div', device=self.dev, parent='test', div=2)
        self.assertTrue(div.enabled())

        div = Divider(name='div', device=self.dev, parent='test',
                      get_div=ext_get_div_zero, div_type=Divider.ZERO_TO_GATE)
        self.assertFalse(div.enabled())

        div = Divider(name='div', device=self.dev, parent='test',
                      get_div=ext_get_div_none)
        self.assertFalse(div.enabled())

def ext_get_freq(pll):
    return 1234

class TestPLL(ClockTestCase):
    def test_enabled(self):
        pll = PLL(name='pll', device=self.dev, get_freq=ext_get_freq,
                  en_field=self.dev.TEST1.TESTA.A3)
        self.dev.TEST1.TESTA.A3.write(1)
        self.assertTrue(pll.enabled())
        self.dev.TEST1.TESTA.A3.write(0)
        self.assertFalse(pll.enabled())

    def test_get_freq(self):
        pll = PLL(name='pll', device=self.dev, get_freq=ext_get_freq)
        self.assertTrue(pll.get_freq(), 1234)

    def test_build(self):
        pll = PLL(device=self.dev)
        self.assertFalse(pll.build())
        pll = PLL(device=self.dev, get_freq=ext_get_freq)
        self.assertTrue(pll.build())

class TestClockTree(ClockTestCase):
    @classmethod
    def setUpClass(self):
        super(TestClockTree, self).setUpClass()
        FixedClock(name='osc1', device=self.dev, freq=1234)
        FixedClock(name='osc2', device=self.dev, freq=2345)
        FixedClock(name='osc3', device=self.dev, freq=5432)
        Mux(name='mux1', device=self.dev, mux_field=self.dev.TEST1.TESTA.A3,
            parents={0: 'osc1', 1: 'osc2', 2: 'osc3', 3: 'osc3'})
        Divider(name='div1', device=self.dev, div=2, parent='osc1')
        Divider(name='div2', device=self.dev, div=4, parent='mux1')
        Gate(name='gate1', device=self.dev, parent='div1',
             en_field=self.dev.TEST1.TESTA.A1)
        Gate(name='gate2', device=self.dev, parent='div2',
             en_field=self.dev.TEST1.TESTA.A2)
        Divider(name='div3', device=self.dev, div=2, parent='gate2')

    def test_get(self):
        self.assertEqual(self.dev.clocktree.get(None), None)
        self.assertEqual(self.dev.clocktree.get('osc3').name, 'osc3')
        with self.assertRaises(UnknownClock):
            self.dev.clocktree.get("unknown clock")

    def test_get_freq(self):
        self.assertEqual(self.dev.clocktree.get_freq('osc3'), 5432)
        self.assertEqual(self.dev.clocktree.get_freq('mux1'), 5432)
        self.assertEqual(self.dev.clocktree.get_freq('div2'), 5432 / 4)
        self.assertEqual(self.dev.clocktree.get_freq('gate2'), 5432 / 4)
        self.assertEqual(self.dev.clocktree.get_freq('div3'), 5432 / 8)
        self.assertEqual(self.dev.clocktree.get_freq('div1'), 1234 / 2)
        self.assertEqual(self.dev.clocktree.get_freq('gate1'), 1234 / 2)
        self.assertEqual(self.dev.clocktree.get_freq(None), 0)
        with self.assertRaises(UnknownClock):
            self.dev.clocktree.get_freq("unknown clock")

    def test_is_gated(self):
        self.dev.TEST1.TESTA.A2.write(1)
        self.assertFalse(self.dev.clocktree.is_gated('gate2'))
        self.assertFalse(self.dev.clocktree.is_gated('div3'))

        self.dev.TEST1.TESTA.A2.write(0)
        self.assertTrue(self.dev.clocktree.is_gated('gate2'))
        self.assertTrue(self.dev.clocktree.is_gated('div3'))
        self.assertTrue(self.dev.clocktree.is_gated(None))

    def test_build(self):
        self.assertTrue(self.dev.clocktree.build())

        Divider(name='div4', device=self.dev)
        self.assertFalse(self.dev.clocktree.build())
        self.dev.clocktree.clocks.pop('div4')

    def test_get_parent(self):
        div3 = self.dev.clocktree.get('div3')
        gate2 = div3.get_parent()
        div2 = gate2.get_parent()
        mux1 = div2.get_parent()
        osc = mux1.get_parent()

        self.assertEqual(gate2.name, 'gate2')
        self.assertEqual(div2.name, 'div2')
        self.assertEqual(mux1.name, 'mux1')
        self.assertEqual(osc.name, 'osc3')

    def test_get_orphans(self):
        orphans = self.dev.clocktree.get_orphans()
        self.assertEqual(len(orphans), 3)
        self.assertIn('osc1', orphans)

    def test_get_children(self):
        children = self.dev.clocktree.get_children("gate2")
        self.assertEqual(len(children), 1)
        self.assertIn('div3', children)

        children = self.dev.clocktree.get_children("div2")
        self.assertEqual(len(children), 1)
        self.assertIn('gate2', children)

        children = self.dev.clocktree.get_children("osc1")
        self.assertEqual(len(children), 2)
        self.assertIn('mux1', children)

    def test_make_tree(self):
        tree = self.dev.clocktree.make_tree()
        self.assertIn('osc1', tree)
        self.assertIn('div1', tree['osc1'])
        self.assertIn('gate1', tree['osc1']['div1'])
        self.assertNotIn('mux1', tree['osc1'])
        self.assertNotIn('mux1', tree['osc2'])
        self.assertIn('mux1', tree['osc3'])

if __name__ == '__main__':
    unittest.main()
