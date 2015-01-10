#!/usr/bin/env python
# Copyright (c) 2013 Federico Ruiz Ugalde
# Author: Federico Ruiz-Ugalde <memeruiz at gmail dot com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# This is a stand alone application. For now it only captures and displays an image after connecting to the device, then it stops.

easycap_dev_id='0x1b71:0x3002'
interface=0

import usb1 as u
from protocol import p_init, p5
from protocol import *
from time import sleep
from fcntl import ioctl
#import v4l2 as v
import os
from time import time, sleep
# import weakref
import numpy as n
import pygame

class Delta_t(object):
    def __init__(self):
        self.old_t=time()

    def update_t(self):
        self.old_t=time()

    def diff_t(self):
        t=time()
        print "Diff t:", t-self.old_t
        self.old_t=t

def variable_for_value(value):
    for n,v in globals().items():
        if v == value:
            return n
    return None

def run_protocol(prot, devh):
    print "TESTST"
    for req_num, req in enumerate(prot):
        print "line", req[0], hex(req[1]), hex(req[2]), hex(req[3]), req[4], req[5],
        if len(req)>6:
            if type(req[6])==list:
                for i,j in req[6]:
                    print hex(i), variable_for_value(j),
            elif type(req[6])==tuple:
                print [hex(i) for i in req[6]],
            else:
                print hex(req[6]),
        #else:
        #    print
        print "req num", req_num
        if req[0][0]=='c':
            if req[0][2:]=='vd':
                print "Control request"
                if req[0][1]=='r':
                    print "Read"
                    reply=devh.controlRead(
                        u.libusb1.LIBUSB_TYPE_VENDOR|u.libusb1.LIBUSB_RECIPIENT_DEVICE,
                        req[1], req[2], req[3], req[5])
                    if len(reply)==1:
                        print "Reply:", hex(ord(reply))
                    else:
                        print "Reply:", [hex(ord(i)) for i in reply]
                        print "Reply char:", reply
                    if type(req[6])==list:
                        print " Multiply options"
                        found_prot=False
                        for resp, next_prot in req[6]:
                            if resp==ord(reply):
                                print "Found response in multiple options, running recursively"
                                print "Jumping to:" , variable_for_value(next_prot)
                                run_protocol(next_prot, devh)
                                found_prot=True
                                break
                        if not found_prot:
                            print "Unknown response!! Exiting!"
                            exit()
                    elif type(req[6])==tuple:
                        print "Long answer"
                        #raw_input()
                        if len(req)==7:
                            if list(req[6])==[ord(i) for i in reply]:
                                print " All fine"
                            else:
                                print " Response incorrect!!! Exiting"
                                exit()
                        elif len(req)==8:
                            print "Some reply may be ignored"
                            for reply, exp_reply, check in zip([ord(i) for i in reply], req[6], req[7]):
                                print "Reply", reply, exp_reply, check
                                if check:
                                    if reply==exp_reply:
                                        print "All fine"
                                    else:
                                        print "Problems with reply!", reply, exp_reply, check
                                        exit()
                                else:
                                    print "Ignored reply"
                            #raw_input()
                    else:
                        if ord(reply)==req[6]:
                            print "All fine!"
                        else:
                            print "Error: Different reply"
                            exit()
                elif req[0][1]=='w':
                    print "Write"
                    reply=devh.controlWrite(
                        u.libusb1.LIBUSB_TYPE_VENDOR|u.libusb1.LIBUSB_RECIPIENT_DEVICE,
                        req[1], req[2], req[3], req[4])
                    print "Reply:", reply
                    if reply==req[5]:
                        print "All fine!"
                    else:
                        print "Error: More data send!"
                        exit()
                else:
                    print "Not supported"


class Utv007(object):
    interface=0
    def __init__(self, device="/dev/video1"):
        self.v4l_device=device
        dev=None
        self.cont=u.USBContext()
        for i in self.cont.getDeviceList():
            print "ID", i.getVendorID(),i.getProductID(), i.getManufacturer(), "Serial: ", i.getSerialNumber(), "Num conf", i.getNumConfigurations()
            if hex(i.getVendorID())+':'+hex(i.getProductID())==easycap_dev_id:
                print "Easycap utv007 found! Dev ID: ", easycap_dev_id
                self.dev=i
                break

        if self.dev:
            print "Openning device"
            self.devh=self.dev.open()
        else:
            print "No easycap utv007 devices found"
            exit()

        while self.devh.kernelDriverActive(self.interface):
            self.devh.detachKernelDriver(self.interface)
            sleep(0.5)
        #if kernel:
        #    print "Kernel driver already using device. Stopping. Kernel:", kernel
        #    exit()

        print "Claiming interface"
        self.devh.claimInterface(self.interface)
        print "Preinit"
        run_protocol(p_preinit, self.devh)
        print "init"
        run_protocol(p_init, self.devh)
        #sleep(1.)
        print
        print "Second part"
        print
        run_protocol(p5, self.devh)
        print "Setting Altsetting to 1"
        self.devh.setInterfaceAltSetting(self.interface,1)
        self.image=[]
        #packet related:
        self.s_packets=''
        #self.s_packets=n.chararray(1, itemsize=960)
        self.expected_toggle=True
        self.expected_n_s_packet=0
        self.expected_n_img=0
        self.start_frame=True
        self.n_packets=0
        #self.v4l_init()
        self.old_t=time()
        self.stop=False
        self.iso=[]
        self.dt=Delta_t()
        #self.test=' '*960
        #self.iso=self.devh.getTransfer(iso_packets=8)
        #self.iso.setIsochronous(0x81, 0x6000, callback=self.callback2, timeout=1000)
        self.failbuf = []
        self.failstuff = []
        self.framebuffer0 = bytearray(720 * 480)
        self.framebuffer1 = bytearray(720 * 480)
        self.framebuffer = bytearray(720 * 480 * 2) # 2 bytes per pixel
        # alternatively 960 * 720
        print "Initialization completed"
        #print "Reading int"
    #a=devh.interruptRead(4,0, timeout=1000)
    #print "Interrupt result" , a

    def __enter__(self):
        print "Enter"
        return(self)

    def __exit__(self, type, value, traceback):
        #for iso in self.iso:
        #    print "STatus", iso.getStatus()
        #del iso
        print "Realeasing interface"
        self.devh.releaseInterface(0)
        print "Closing device handler"
        self.devh.close()
        #sleep(2)
        print "Exiting context"
        self.cont.exit()
        pass

    def __del__(self):
        print "Deleting"

    def do_iso2(self):
        #print "Submitting another iso"
        iso=self.devh.getTransfer(iso_packets=8)
        iso.setIsochronous(0x81, buffer_or_len=0x6000, callback=self.callback2)
        iso.submit()
        self.iso.append(iso)
        #self.iso.setCallback(callback1)


    def handle_ev(self):
        #print "Event a"
        #sleep(10)
        self.cont.handleEvents()
        #print "Event b"

    def get_useful_data(self, buffer_list, setup_list):
        data=''
        for b, s in zip(buffer_list, setup_list):
            actual_len=s['actual_length']
            print "Actual len" , actual_len
            data+=b[:actual_len]
        return(data)

    def build_images(self, buffer_list, setup_list):
        """ buffer_list is a list that contains around 8 packets inside, each of this packets contains 3 smaller packets inside
        The first four bytes of this s_packets are special:
        1) 0x88 always
        2) frame counter
        3) 8bit: toogle frame bit (for interlacing), 7-0bits packet counter
        4) packet counter
        With frame counter one can know if we are loosing frames
        With the packet counter one can know if we have incomplete frames
        With the toogle frame bit it is possible to generate the correct complete progressive image
        This four bytes must be removed from the image data.
        The last 60 bytes are black filled (for synchronization?) and must be removed
        Each s_packet is 1024 long but once we remove this bytes the data payload is 1024-4-60=960 bytes long.
        If packet starts with 0x00 instead of 0x88, it means it is empty and to be ignored

        In this routine we find the start of first of the two interlaced images, and then we start processing
"""
        packets=[self.buffer_list[i][:int(self.setup_list[i]['actual_length'])] for i in xrange(len(self.buffer_list))]
        #print "n packets", len(packets)
        
        for packet in packets:
            #print [hex(ord(i)) for i in packet[:4]]
            #print [hex(ord(i)) for i in packet[len(packet)/3:len(packet)/3+4]]
            #print [hex(ord(i)) for i in packet[2*len(packet)/3:2*len(packet)/3+4]]
            #if [hex(ord(i)) for i in packet[:4]]==['0x0', '0x0', '0x0', '0x0'] or [hex(ord(i)) for i in packet[len(packet)/3:len(packet)/3+4]]==['0x0', '0x0', '0x0', '0x0'] or [hex(ord(i)) for i in packet[2*len(packet)/3:2*len(packet)/3+4]]==['0x0', '0x0', '0x0', '0x0']:
                #print "special packet"
            #    pass
            if len(packet) == 0:
                continue
            #self.dt.update_t()
            for s_packet in [packet[:len(packet)/3], packet[len(packet)/3:2*len(packet)/3], packet[2*len(packet)/3:len(packet)]]:
                if ord(s_packet[0]) != 0x88:
                    continue
                n_img=ord(s_packet[1])
                n_s_packet=((ord(s_packet[2]) & 0x0f)<< 8) | (ord(s_packet[3]))
                n_toggle=(((ord(s_packet[2]) & 0xf0) >> 7) == 0)

                # s_packet[4:1024-60]
                # n = (n_s_packet) * 960
                n = (n_s_packet + int(not n_toggle) * 360) * 960
                # n = n_s_packet * 480
                # n = 360 * 20
                self.framebuffer[n: n + 960] = s_packet[4:1024-60]

                # n = (2 * n_s_packet + 1) * 960
                # self.framebuffer[n: n + 960] = s_packet[4:1024-60]

                if n_toggle == False and n_s_packet == 359:
                    # self.display_frame()
                    print camclock.get_fps()
                    camclock.tick()
                    # self.framebuffer = bytearray(720 * 480 * 2)


    def callback2(self, transfer):
        #print "Callback"
        self.buffer_list=transfer.getISOBufferList()
        self.setup_list=transfer.getISOSetupList()
        self.status=transfer.getStatus()
        #print "Status" , self.status
        self.build_images(self.buffer_list, self.setup_list)
        #del transfer
        #transfer.close()
        if not self.stop:
            transfer.submit()
        else:
            print "Sending no more submits"
        # self.do_iso2()


    def display_frame(self):
        # deinterlace
        out = ''

        start = time()
        # for i in xrange(480/2):
        #     out += self.s_packets[i*1440:(i+1)*1440]
        #     out += self.s_packets[(i+480/2)*1440:(i+480/2+1)*1440]
        
        # r = np.fromstring(out, dtype='uint8')

        yuyv = np.reshape(self.framebuffer, (len(self.framebuffer) / 4, 4))
        # yuyv = r.reshape((len(r) / 4, 4))
        together = np.vstack((yuyv[:,0], yuyv[:,1], yuyv[:,3], yuyv[:,2], yuyv[:,1], yuyv[:,3])).T.reshape((480, 720 * 3))
        # print together
        # deinterlaced = bytearray(720 * 3 * 480)
        # deinterlaced = np.zeros(720 * 3 * 480)
        # for i in range(480):
        #     # print len(together[i, :].flatten())
        #     deinterlaced[720 * 3 * i: 720 * 3 * (i + 1)] = together[i, :].flatten()
        deinterlaced = np.zeros((480, 720 * 3), dtype='uint8')
        # deinterlaced[:,:] = together[:,:]
        # deinterlaced[:] = together[:]
        deinterlaced[::2 ,:] = together[:240,:]
        deinterlaced[1::2,:] = together[240:,:] 
        # deinterlaced[:240,:] = together[:240,:]


        # together = np.vstack((yuyv[:,0], zeros(480), zeros(480),yuyv[:,2], zeros(480), zeros(480)))
        size = (720, 480)
        im = Image.frombuffer("YCbCr", size, deinterlaced.flatten()).transpose(Image.FLIP_TOP_BOTTOM).convert('RGB')

        # size = (1440, 480)
        # im = Image.frombuffer("L", size, self.framebuffer).convert('RGB')


        # im = Image.frombuffer("L", size, np.vstack((yuyv[:,0], yuyv[:,2])).T.flatten()).convert('RGB')        
        # im = Image.frombuffer("L", (720, 480), yuyv[:,0].flatten()).convert('RGB')

        surface = pygame.image.fromstring(im.tostring(), size, "RGB")
        screen.blit(surface, (0,0)) 
        
        font = pygame.font.Font(None, 36)
        text = font.render("FPS: %1.1f" % renclock.get_fps(), 1, (90, 10, 10))
        screen.blit(text, (10, 10))
        print "fps", renclock.get_fps()

        pygame.display.flip()
        renclock.tick()

        # print time() - start
        # im.show()
        # exit()

        # together.T.flatten()
        # image3.append((0, 0, 0, ba.array('B', together.T.flatten()).tostring()))
        

import array as ba
import numpy as np


def change_res(images):
    width=640
    new_images=[]
    for img, size in images:
        new_img=''
        for i in xrange(size[1]):
            new_img=img[i*size[0]: i*size[0]+width*3]+new_img
        new_images.append((new_img, (width*3, size[1])))
    return(new_images)

from fcntl import ioctl
#import v4l2 as v
import os
from time import time, sleep

# def send_loopback(images):
    
#     d=os.open("/dev/video1", os.O_RDWR)
#     cap=v.v4l2_capability()
#     ioctl(d, v.VIDIOC_QUERYCAP, cap)
#     vid_format=v.v4l2_format()
#     #ioctl(d, v.VIDIOC_G_FMT, vid_format)
#     vid_format.type=v.V4L2_BUF_TYPE_VIDEO_OUTPUT
#     vid_format.fmt.pix.width=640
#     #vid_format.fmt.pix.sizeimage=1036800
#     vid_format.fmt.pix.height=480
#     vid_format.fmt.pix.pixelformat=v.V4L2_PIX_FMT_RGB24
#     vid_format.fmt.pix.field=v.V4L2_FIELD_NONE
#     vid_format.fmt.pix.colorspace=v.V4L2_COLORSPACE_SRGB
#     ioctl(d, v.VIDIOC_S_FMT, vid_format)
#     print "frame size", vid_format.fmt.pix.sizeimage, len(images[0][0]), images[0][1]
#     raw_input()
#     counter=0
#     old_t=time()
#     fps_period=1./29.97
#     while True:
#         counter+=1
#         #print "Image", counter
#         for img, size in images:
#             t=time()
#             delta_time=t-old_t
#             print "Delta", delta_time,
#             old_t=t
#             if delta_time<fps_period:
#                 print "sleeping a bit"
#                 sleep(fps_period-delta_time)
#             os.write(d, img)

from PIL import Image
import struct

quit_now=False

def signal_handler(signal, frame):
    print 'You pressed Ctrl+C!'
    global quit_now
    quit_now=True

screen = None
renclock = pygame.time.Clock()
camclock = pygame.time.Clock()

import signal
def main():
    signal.signal(signal.SIGINT, signal_handler)

    pygame.init()
    size = (720*2, 480*2)
    global screen

    screen = pygame.display.set_mode(size)
    pygame.display.set_caption("My Game")
    
    with Utv007() as utv:
        for i in xrange(20):
            utv.do_iso2()
        
        while not quit_now:
            utv.handle_ev()
        
        print "closing utv"
        utv.stop=True




if __name__=="__main__":
    main()