#!/usr/bin/env python
# Copyright (c) 2013 Federico Ruiz Ugalde
# Copyright (c) 2014 Kevin Kwok
# 
# Author: Federico Ruiz-Ugalde <memeruiz at gmail dot com>
# Author: Kevin Kwok <antimatter15@gmail.com>
# Updated for Python 3, FFMPEG and Apple Silicon by Richard Arnez James
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import usb1
from time import sleep, strftime
import pygame
import numpy as np
from PIL import Image
import threading
import signal
import sys
import subprocess # Use subprocess to pipe frames to FFmpeg

# ==============================================================================
# == Integrated Protocol Data from protocol.py
# ==============================================================================

def variable_for_value(value):
    """A debug helper to find the name of the protocol list variable."""
    for n, v in globals().items():
        if v == value:
            return n
    return None

def run_protocol(prot, devh):
    """
    Executes a list of USB control transfer commands.
    This function recursively calls itself if the protocol branches based on device responses.
    """
    for req_num, req in enumerate(prot):
        if req[0][0] == 'c':
            if req[0][2:] == 'vd':
                bmRequestType = usb1.libusb1.LIBUSB_TYPE_VENDOR | usb1.libusb1.LIBUSB_RECIPIENT_DEVICE
                bRequest, wValue, wIndex = req[1], req[2], req[3]
                if req[0][1] == 'r':
                    reply = devh.controlRead(bmRequestType, bRequest, wValue, wIndex, req[5])
                    if isinstance(req[6], list):
                        found_prot = False
                        reply_byte = reply[0]
                        for resp, next_prot in req[6]:
                            if resp == reply_byte:
                                run_protocol(next_prot, devh)
                                found_prot = True
                                break
                        if not found_prot:
                            print(f"  [ERROR] Unknown response: {hex(reply_byte)}. Cannot continue.")
                            sys.exit(1)
                elif req[0][1] == 'w':
                    devh.controlWrite(bmRequestType, bRequest, wValue, wIndex, req[4])

# --- Protocol sequence data structures (omitted for brevity) ---
p4a=[['cwvd', 0x0c, 0x0010, 0xf891, b'', 0]]
p4=[['cwvd', 0x0c, 0x00a6, 0xc27d, b'', 0],['cwvd', 0x0c, 0x0011, 0xc280, b'', 0],['cwvd', 0x0c, 0x0040, 0xc281, b'', 0],['cwvd', 0x0c, 0x0011, 0xc282, b'', 0],['cwvd', 0x0c, 0x0040, 0xc283, b'', 0],['crvd', 0x0b, 0x0000, 0xf891, b'', 1, [(0x10, p4a), (0x30, p4a)]]]
p3a=[['cwvd', 0x0c, 0x0002, 0xc27d, b'', 0],['cwvd', 0x0c, 0x0006, 0xc27d, b'', 0],['cwvd', 0x0c, 0x0026, 0xc27d, b'', 0],['cwvd', 0x0c, 0x0026, 0xc27d, b'', 0]]+p4
p3b=[['cwvd', 0x0c, 0x00a6, 0xc27d, b'', 0],['cwvd', 0x0c, 0x00a6, 0xc27d, b'', 0],['cwvd', 0x0c, 0x00a6, 0xc27d, b'', 0],['cwvd', 0x0c, 0x00a6, 0xc27d, b'', 0]]+p4
p2c=[['cwvd', 0x0c, 0x0086, 0xf894, b'', 0],['cwvd', 0x0c, 0x00c0, 0xc0ac, b'', 0],['cwvd', 0x0c, 0x0000, 0xc0ad, b'', 0],['cwvd', 0x0c, 0x0012, 0xc0a2, b'', 0],['cwvd', 0x0c, 0x00e0, 0xc0a3, b'', 0],['cwvd', 0x0c, 0x0028, 0xc0a4, b'', 0],['cwvd', 0x0c, 0x0082, 0xc0a5, b'', 0],['cwvd', 0x0c, 0x0080, 0xc0a7, b'', 0],['cwvd', 0x0c, 0x0014, 0xc000, b'', 0],['cwvd', 0x0c, 0x0003, 0xc006, b'', 0],['cwvd', 0x0c, 0x0099, 0xc090, b'', 0],['cwvd', 0x0c, 0x0090, 0xc091, b'', 0],['cwvd', 0x0c, 0x0068, 0xc094, b'', 0],['cwvd', 0x0c, 0x0070, 0xc095, b'', 0],['cwvd', 0x0c, 0x0030, 0xc09c, b'', 0],['cwvd', 0x0c, 0x00c0, 0xc09d, b'', 0],['cwvd', 0x0c, 0x00e0, 0xc09e, b'', 0],['cwvd', 0x0c, 0x0006, 0xc019, b'', 0],['cwvd', 0x0c, 0x00ba, 0xc08c, b'', 0],['cwvd', 0x0c, 0x00ff, 0xc101, b'', 0],['cwvd', 0x0c, 0x00b3, 0xc10c, b'', 0],['cwvd', 0x0c, 0x0080, 0xc1b2, b'', 0],['cwvd', 0x0c, 0x00a0, 0xc1b4, b'', 0],['cwvd', 0x0c, 0x00ff, 0xc14c, b'', 0],['cwvd', 0x0c, 0x00ca, 0xc14d, b'', 0],['cwvd', 0x0c, 0x0053, 0xc113, b'', 0],['cwvd', 0x0c, 0x008a, 0xc119, b'', 0],['cwvd', 0x0c, 0x0003, 0xc13c, b'', 0],['cwvd', 0x0c, 0x009c, 0xc150, b'', 0],['cwvd', 0x0c, 0x0071, 0xc151, b'', 0],['cwvd', 0x0c, 0x00c6, 0xc152, b'', 0],['cwvd', 0x0c, 0x0084, 0xc153, b'', 0],['cwvd', 0x0c, 0x00bc, 0xc154, b'', 0],['cwvd', 0x0c, 0x00a0, 0xc155, b'', 0],['cwvd', 0x0c, 0x00a0, 0xc156, b'', 0],['cwvd', 0x0c, 0x009c, 0xc157, b'', 0],['cwvd', 0x0c, 0x001f, 0xc158, b'', 0],['cwvd', 0x0c, 0x0006, 0xc159, b'', 0],['cwvd', 0x0c, 0x0000, 0xc15d, b'', 0],['crvd', 0x0b, 0x0000, 0xc27d, b'', 1, [(0x00,p3a),(0xa6,p3b)]]]
p2a=[['cwvd', 0x0c, 0x000c, 0xf890, b'', 0],['crvd', 0x0b, 0x0000, 0xf894, b'', 1, 0x86]]+p2c
p2b=[['cwvd', 0x0c, 0x000c, 0xf890, b'', 0],['crvd', 0x0b, 0x0000, 0xf894, b'', 1, 0x87]]+p2c
p2=[['cwvd', 0x0c, 0x0032, 0xc27a, b'', 0],['crvd', 0x0b, 0x0000, 0xf890, b'', 1, [(0x0c, p2a), (0x8c, p2b)]]]
p1aa=[['cwvd', 0x0c, 0x0030, 0xc27a, b'', 0],['cwvd', 0x0c, 0x0030, 0xc27a, b'', 0],['cwvd', 0x0c, 0x0032, 0xc27a, b'', 0],]+p2
p1ab=[['cwvd', 0x0c, 0x0000, 0xc27a, b'', 0],['cwvd', 0x0c, 0x0010, 0xc27a, b'', 0],['cwvd', 0x0c, 0x0012, 0xc27a, b'', 0]]+p2
p1a=[['cwvd', 0x0c, 0x0009, 0xc278, b'', 0],['cwvd', 0x0c, 0x000d, 0xc278, b'', 0],['cwvd', 0x0c, 0x002d, 0xc278, b'', 0],['crvd', 0x0b, 0x0000, 0xc279, b'', 1, 0x00],['cwvd', 0x0c, 0x0002, 0xc279, b'', 0],['cwvd', 0x0c, 0x000a, 0xc279, b'', 0],['crvd', 0x0b, 0x0000, 0xc27a, b'', 1, [(0x30, p1aa), (0x00, p1ab)]]]
p1b=[['cwvd', 0x0c, 0x002d, 0xc278, b'', 0],['cwvd', 0x0c, 0x002d, 0xc278, b'', 0],['cwvd', 0x0c, 0x002d, 0xc278, b'', 0],['crvd', 0x0b, 0x0000, 0xc279, b'', 1, 0x0a],['cwvd', 0x0c, 0x000a, 0xc279, b'', 0],['cwvd', 0x0c, 0x000a, 0xc279, b'', 0],['crvd', 0x0b, 0x0000, 0xc27a, b'', 1, 0x32],['cwvd', 0x0c, 0x0032, 0xc27a, b'', 0],['cwvd', 0x0c, 0x0032, 0xc27a, b'', 0]]+p2
p_init=[['crvd', 0x0b, 0x0000, 0xc278, b'', 1, [(0x08, p1a), (0x2d, p1b)]]]
p_preinit=[['crvd', 0x02, 0x00a0, 0x00f0, b'', 2, (0x01, 0xdb), (True, False)],['cwvd', 0x0c, 0x0001, 0xc008, b'', 0],['cwvd', 0x0c, 0x00ff, 0xc1d0, b'', 0],['cwvd', 0x0c, 0x0002, 0xc1d9, b'', 0],['cwvd', 0x0c, 0x0013, 0xc1da, b'', 0],['cwvd', 0x0c, 0x0012, 0xc1db, b'', 0],['cwvd', 0x0c, 0x0002, 0xc1e9, b'', 0],['cwvd', 0x0c, 0x006c, 0xc1ec, b'', 0],['cwvd', 0x0c, 0x0030, 0xc25b, b'', 0],['cwvd', 0x0c, 0x0073, 0xc254, b'', 0],['cwvd', 0x0c, 0x0020, 0xc294, b'', 0],['cwvd', 0x0c, 0x00cf, 0xc255, b'', 0],['cwvd', 0x0c, 0x0020, 0xc256, b'', 0],['cwvd', 0x0c, 0x0030, 0xc1eb, b'', 0],['cwvd', 0x0c, 0x0060, 0xc105, b'', 0],['cwvd', 0x0c, 0x00f2, 0xc11f, b'', 0],['cwvd', 0x0c, 0x0060, 0xc127, b'', 0],['cwvd', 0x0c, 0x0010, 0xc0ae, b'', 0],['cwvd', 0x0c, 0x00aa, 0xc284, b'', 0],['cwvd', 0x0c, 0x0004, 0xc003, b'', 0],['cwvd', 0x0c, 0x0068, 0xc01a, b'', 0],['cwvd', 0x0c, 0x00d3, 0xc100, b'', 0],['cwvd', 0x0c, 0x0072, 0xc10e, b'', 0],['cwvd', 0x0c, 0x00a2, 0xc10f, b'', 0],['cwvd', 0x0c, 0x00b0, 0xc112, b'', 0],['cwvd', 0x0c, 0x0015, 0xc115, b'', 0],['cwvd', 0x0c, 0x0001, 0xc117, b'', 0],['cwvd', 0x0c, 0x002c, 0xc118, b'', 0],['cwvd', 0x0c, 0x0010, 0xc12d, b'', 0],['cwvd', 0x0c, 0x0020, 0xc12f, b'', 0],['cwvd', 0x0c, 0x002e, 0xc220, b'', 0],['cwvd', 0x0c, 0x0008, 0xc225, b'', 0],['cwvd', 0x0c, 0x0002, 0xc24e, b'', 0],['cwvd', 0x0c, 0x0002, 0xc24f, b'', 0],['cwvd', 0x0c, 0x0059, 0xc254, b'', 0],['cwvd', 0x0c, 0x0016, 0xc25a, b'', 0],['cwvd', 0x0c, 0x0035, 0xc25b, b'', 0],['cwvd', 0x0c, 0x0017, 0xc263, b'', 0],['cwvd', 0x0c, 0x0016, 0xc266, b'', 0],['cwvd', 0x0c, 0x0036, 0xc267, b'', 0],['cwvd', 0x0c, 0x0002, 0xc24e, b'', 0],['cwvd', 0x0c, 0x0002, 0xc24f, b'', 0],['cwvd', 0x0c, 0x0040, 0xc239, b'', 0],['cwvd', 0x0c, 0x0000, 0xc240, b'', 0],['cwvd', 0x0c, 0x0000, 0xc241, b'', 0],['cwvd', 0x0c, 0x0002, 0xc242, b'', 0],['cwvd', 0x0c, 0x0080, 0xc243, b'', 0],['cwvd', 0x0c, 0x0012, 0xc244, b'', 0],['cwvd', 0x0c, 0x0090, 0xc245, b'', 0],['cwvd', 0x0c, 0x0000, 0xc246, b'', 0]]
p7=[['crvd', 0x0b, 0x0000, 0xc245, b'', 1, 0x90],['crvd', 0x0b, 0x0000, 0xc242, b'', 1, 0x02],['crvd', 0x0b, 0x0000, 0xc243, b'', 1, 0x80],['crvd', 0x0b, 0x0000, 0xc240, b'', 1, 0x00],['crvd', 0x0b, 0x0000, 0xc241, b'', 1, 0x00],['cwvd', 0x0c, 0x0004, 0xc003, b'', 0],['cwvd', 0x0c, 0x0079, 0xc01a, b'', 0],['cwvd', 0x0c, 0x00d3, 0xc100, b'', 0],['cwvd', 0x0c, 0x0068, 0xc10e, b'', 0],['cwvd', 0x0c, 0x009c, 0xc10f, b'', 0],['cwvd', 0x0c, 0x00f0, 0xc112, b'', 0],['cwvd', 0x0c, 0x0015, 0xc115, b'', 0],['cwvd', 0x0c, 0x0000, 0xc117, b'', 0],['cwvd', 0x0c, 0x00fc, 0xc118, b'', 0],['cwvd', 0x0c, 0x0004, 0xc12d, b'', 0],['cwvd', 0x0c, 0x0008, 0xc12f, b'', 0],['cwvd', 0x0c, 0x002e, 0xc220, b'', 0],['cwvd', 0x0c, 0x0008, 0xc225, b'', 0],['cwvd', 0x0c, 0x0002, 0xc24e, b'', 0],['cwvd', 0x0c, 0x0001, 0xc24f, b'', 0],['cwvd', 0x0c, 0x005f, 0xc254, b'', 0],['cwvd', 0x0c, 0x0012, 0xc25a, b'', 0],['cwvd', 0x0c, 0x0001, 0xc25b, b'', 0],['cwvd', 0x0c, 0x001c, 0xc263, b'', 0],['cwvd', 0x0c, 0x0011, 0xc266, b'', 0],['cwvd', 0x0c, 0x0005, 0xc267, b'', 0],['cwvd', 0x0c, 0x0002, 0xc24e, b'', 0],['cwvd', 0x0c, 0x0002, 0xc24f, b'', 0],['cwvd', 0x0c, 0x00b8, 0xc16f, b'', 0],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['cwvd', 0x0c, 0x0060, 0xc105, b'', 0],['cwvd', 0x0c, 0x00f2, 0xc11f, b'', 0],['cwvd', 0x0c, 0x0060, 0xc127, b'', 0],['cwvd', 0x0c, 0x0010, 0xc0ae, b'', 0],['cwvd', 0x0c, 0x00aa, 0xc284, b'', 0],['cwvd', 0x0c, 0x0060, 0xc105, b'', 0],['cwvd', 0x0c, 0x00f2, 0xc11f, b'', 0],['cwvd', 0x0c, 0x0060, 0xc127, b'', 0],['cwvd', 0x0c, 0x0010, 0xc0ae, b'', 0],['cwvd', 0x0c, 0x00aa, 0xc284, b'', 0]]
p6b=[['cwvd', 0x0c, 0x0060, 0xc105, b'', 0],['cwvd', 0x0c, 0x00f2, 0xc11f, b'', 0],['cwvd', 0x0c, 0x0060, 0xc127, b'', 0],['cwvd', 0x0c, 0x0010, 0xc0ae, b'', 0],['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0xaa],['cwvd', 0x0c, 0x0088, 0xc284, b'', 0],['crvd', 0x0b, 0x0000, 0xc244, b'', 1, 0x12],['crvd', 0x0b, 0x0000, 0xc246, b'', 1, 0x00],['crvd', 0x0b, 0x0000, 0xc244, b'', 1, 0x12]]+p7
p6a=[['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, 0x88],['crvd', 0x0b, 0x0000, 0xc244, b'', 1, 0x11],['crvd', 0x0b, 0x0000, 0xc246, b'', 1, 0xcd],['crvd', 0x0b, 0x0000, 0xc244, b'', 1, 0x11]]+p7
p5=[['crvd', 0x0b, 0x0000, 0xc0ae, b'', 1, 0x10],['crvd', 0x0b, 0x0000, 0xc284, b'', 1, [(0x88, p6a), (0xaa, p6b)]]]


# ==============================================================================
# == Main Application Logic
# ==============================================================================

# --- Device Identification ---
KNOWN_DEVICES = [
    (0x1b71, 0x3002),  # Fushicai USBTV007
    (0xeb1a, 0x2861),  # eMPIA Technology, Inc.
]

# --- Global state variables ---
quit_now = False
screen = None
record = None # Will hold the FFmpeg subprocess object
renclock = pygame.time.Clock()
camclock = pygame.time.Clock()

class Utv007:
    interface = 0

    def __init__(self):
        self.cont = usb1.USBContext()
        self.dev = None
        self.devh = None

        print("Searching for USBTV007 device...")
        for device_obj in self.cont.getDeviceList(skip_on_error=True):
            vid = device_obj.getVendorID()
            pid = device_obj.getProductID()
            if (vid, pid) in KNOWN_DEVICES:
                print(f"Found device: VID={hex(vid)}, PID={hex(pid)}")
                self.dev = device_obj
                break
        
        if self.dev:
            print("Opening device...")
            self.devh = self.dev.open()
        else:
            print("[ERROR] No EasyCAP UTV007 devices found. Exiting.")
            sys.exit(1)
        
        print("Attempting to detach kernel driver...")
        try:
            if self.devh.kernelDriverActive(self.interface):
                self.devh.detachKernelDriver(self.interface)
                print("Kernel driver detached.")
        except usb1.USBError as e:
            print(f"Could not detach kernel driver (this is often normal): {e}")

        print("Claiming interface...")
        self.devh.claimInterface(self.interface)
        
        print("Running Pre-initialization sequence...")
        run_protocol(p_preinit, self.devh)
        print("Running Initialization sequence...")
        run_protocol(p_init, self.devh)
        run_protocol(p5, self.devh)
        
        print("Setting Altsetting to 1 to start isochronous stream...")
        self.devh.setInterfaceAltSetting(self.interface, 1)

        self.stop = False
        self.iso_transfers = []
        self.framebuffer = bytearray(720 * 480 * 2)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("\nExiting UTV007 context...")
        for iso in self.iso_transfers:
            if iso.isSubmitted():
                try: iso.cancel()
                except usb1.USBError: pass
        
        try: self.devh.releaseInterface(self.interface)
        except usb1.USBError: pass
            
        self.devh.close()
        self.cont.close()
        print("Cleanup complete.")

    def submit_iso_transfer(self):
        iso = self.devh.getTransfer(iso_packets=8)
        iso.setIsochronous(0x81, 0x6000, callback=self.process_data_callback)
        iso.submit()
        self.iso_transfers.append(iso)

    def handle_events(self):
        self.cont.handleEvents()

    def build_frame(self, buffer_list, setup_list):
        packets = [buffer_list[i][:int(setup_list[i]['actual_length'])] for i in range(len(buffer_list))]
        for packet in packets:
            if not packet or len(packet) == 0: continue
            s_packet_len = len(packet) // 3 
            for i in range(3):
                s_packet = packet[i*s_packet_len : (i+1)*s_packet_len]
                if not s_packet or s_packet[0] != 0x88: continue
                n_s_packet = ((s_packet[2] & 0x0f) << 8) | s_packet[3]
                n_toggle = (((s_packet[2] & 0xf0) >> 7) == 0)
                offset = (n_s_packet + int(not n_toggle) * 360) * 960
                self.framebuffer[offset : offset + 960] = s_packet[4:1024-60]
                if n_toggle is False and n_s_packet == 359:
                    camclock.tick()

    def process_data_callback(self, transfer):
        self.build_frame(transfer.getISOBufferList(), transfer.getISOSetupList())
        if not self.stop:
            transfer.submit()

def convert_frame_to_rgb(framebuffer):
    yuyv = np.frombuffer(framebuffer, dtype=np.uint8).reshape((480 * 720 * 2 // 4, 4))
    together = np.vstack((yuyv[:,0], yuyv[:,1], yuyv[:,3], yuyv[:,2], yuyv[:,1], yuyv[:,3])).T.reshape((480, 720 * 3))
    deinterlaced = np.zeros((480, 720 * 3), dtype='uint8')
    deinterlaced[1::2 ,:] = together[:240,:]
    deinterlaced[::2,:] = together[240:,:]
    im = Image.frombytes("YCbCr", (720, 480), deinterlaced.tobytes(), 'raw', 'YCbCr', 0, 1).convert('RGB')
    return im

def display_frame(im):
    surface = pygame.image.fromstring(im.tobytes(), (720, 480), "RGB")
    screen.blit(surface, (0,0))
    font = pygame.font.Font(None, 36)
    fps_text = font.render(f"Capture FPS: {camclock.get_fps():.1f}", True, (190, 10, 10))
    screen.blit(fps_text, (10, 10))
    if record is not None:
        rec_text = font.render("REC", True, (255, 0, 0))
        screen.blit(rec_text, (650, 10))
    else:
        rec_text = font.render("Recording Stopped", True, (190, 10, 10))
        screen.blit(rec_text, (500, 450))
    pygame.display.flip()
    renclock.tick()

class ListenThread(threading.Thread):
    def __init__(self, utv):
        super().__init__()
        self.utv = utv
        self._stop_event = threading.Event()
    def stop(self):
        self._stop_event.set()
    def run(self):
        for _ in range(20): self.utv.submit_iso_transfer()
        while not self._stop_event.is_set(): self.utv.handle_events()

def signal_handler(sig, frame):
    global quit_now
    print("\nCtrl+C detected! Shutting down...")
    quit_now = True

def main():
    signal.signal(signal.SIGINT, signal_handler)
    pygame.init()
    
    global screen, quit_now, record
    size = (720, 480)
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption("Fushicai EasyCAP - Hardware Accelerated Recording")

    try:
        with Utv007() as utv:
            lt = ListenThread(utv)
            lt.start()

            # --- Start Recording Immediately ---
            filename = strftime("Recording-%Y-%m-%d-%H.%M.%S.mp4")
            print(f"🚀 Starting HARDWARE-ACCELERATED recording to {filename}...")
            print("   Press 'r' to stop recording, or close the window to stop and exit.")

            command = [
                'ffmpeg',
                '-y',
                '-f', 'rawvideo',
                '-vcodec', 'rawvideo',
                '-pix_fmt', 'rgb24',
                '-s', f'{size[0]}x{size[1]}',
                '-framerate', '50',
                '-i', '-',
                # --- MODIFIED SECTION ---
                '-c:v', 'h264_videotoolbox', # Use the Apple VideoToolbox hardware encoder
                '-b:v', '5M',                # Set a video bitrate (e.g., 5 Megabits/sec). Adjust if needed.
                '-allow_sw', '1',            # Allow software processing for pixel format conversion if necessary
                # --- END MODIFICATION ---
                filename
            ]
            
            record = subprocess.Popen(
                command, 
                stdin=subprocess.PIPE, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )

            while not quit_now:
                im = convert_frame_to_rgb(utv.framebuffer)
                display_frame(im)

                if record is not None:
                    try: record.stdin.write(im.tobytes())
                    except (BrokenPipeError, IOError):
                        print("[ERROR] FFmpeg pipe broke. Stopping recording.")
                        record.wait()
                        record = None
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        quit_now = True
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            if record is not None:
                                print("🛑 Finishing recording by key press.")
                                if record.stdin: record.stdin.close()
                                record.wait()
                                record = None
                            else:
                                print("Recording has already been stopped.")
                        elif event.key == pygame.K_SPACE:
                            screen.fill((255, 255, 255))
                            pygame.display.flip()
                            filename = strftime("Snapshot-%Y-%m-%d-%H.%M.%S.jpg")
                            im.save(filename)
                            print(f"📸 Saving snapshot as {filename}")

            print("Main loop finished. Stopping threads...")
            utv.stop = True
            lt.stop()
            lt.join()

    except Exception as e:
        print(f"\n[FATAL ERROR] An unexpected error occurred: {e}")
    finally:
        if record is not None:
            print("Application is quitting, finalizing recording...")
            if record.stdin: record.stdin.close()
            record.wait()
        
        pygame.quit()
        print("Application terminated.")

if __name__ == "__main__":
    main()