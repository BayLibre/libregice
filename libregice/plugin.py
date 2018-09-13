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

from libregice import RegiceOpenOCD, RegiceJLink, RegiceClientTest
from libregice.device import Device
from regicecommon.helpers import load_svd
from regicecommon.pkg import get_compatible_module


def init_args(parser):
    """
        Add arguments required to init libregice.
    """
    parser.add_argument(
        "--svd",
        help="SVD file that contains registers definition"
    )

    parser.add_argument(
        "--openocd", action='store_true',
        help="Use openocd to connect to target"
    )

    group = parser.add_argument_group('jlink')
    group.add_argument(
        "--jlink", action='store_true',
        help="Use JLink to connect to target"
    )
    group.add_argument(
        "--jlink-script", default=None,
        help="Load and run a JLink script before to connect to target"
    )
    group.add_argument(
        "--jlink-device", default=None,
        help="Name of device to connect to"
    )

    parser.add_argument(
        "--test", action='store_true',
        help="Use a mock as target"
    )

def process_args(unused, args):
    """
        Process arguments to allocate a Device object

        The allocate a RegiceClient, load the SVD file in order to allocate
        a Device object.

        :param unused: Not used, usually a None object
        :param args: Parsed arguments from ArgumentParser
        :return: A dictionary that contains svd, client and device objects
    """
    if args.openocd:
        client = RegiceOpenOCD()
    if args.jlink:
        client = RegiceJLink(args)
    if args.test:
        client = RegiceClientTest()

    svd = load_svd(args.svd)
    module = get_compatible_module(svd.name)
    if module:
        device = module.device_init(svd, client)
    else:
        device = Device(svd, client)

    return {'device': device, 'svd': svd, 'client': client}
