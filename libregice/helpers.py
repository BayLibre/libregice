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

"""
    Provide some functions that may be common between project using libregice.

    In order to avoid code duplication, provide some functions to do common tasks
    such as configuring argparse arguments, allocating regice and loading SVD.
"""

from libregice import Regice, RegiceOpenOCD, RegiceJLink, RegiceClientTest

def regice_add_arguments(parser):
    """
       Add common regice arguments

       This adds some arguments to the parser to select and configure the
       regice client.

       :param parser: The argument parser to setup
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

def regice_alloc(args):
    """
        Allocate and init regice

        This allocate regice and init it using the arguments provided by user.
        :param args: The arguments (parsed by argparse) to use to setup regice
    """
    if args.openocd:
        client = RegiceOpenOCD()
    if args.jlink:
        client = RegiceJLink(args)
    if args.test:
        client = RegiceClientTest()

    regice = Regice(client)

    if args.svd:
        regice.load_svd(args.svd)

    return regice
