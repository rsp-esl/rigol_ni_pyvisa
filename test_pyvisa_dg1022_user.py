#!/usr/bin/env python

############################################################################
# Date: 2017-11-16
############################################################################
# Author: Rawat S. 
#   (Dept. of Electrical & Computer Engineering, KMUTNB, Bangkok/Thailand)
#
############################################################################
# Short Description:
#   This Python script is used to demonstrate how to program 
#   the Rigol DG1022 function generator via USB. 
#   When programmed, the DG1022 device outputs a periodic waveform signal
#   on the output channel 1. The generated waveform is specified by 
#   the uploaded data array consisting of 1024 integers between 0 to 16393.
# 
#   This code relies on the NI VISA interface / driver. 
#   (Make sure that the proper NI VISA driver has been installed correctly.)
#
############################################################################
# Usage:
#   Don't forget to install pyusb and pyvisa packages:
#   (When using Linux/Ubuntu, don't forget to use the sudo command).
# 
#   $ pip install pyusb -U
#   $ pip install pyvisa -U
#   $ pip install pyvisa-py -U
#
#   To run the script under Linux (e.g. Ubuntu)
#   (When using Linux/Ubuntu, don't forget to use the sudo command).
#
#   $ python2  ./test_pyvisa_dg1022_user.py
#   $ python3  ./test_pyvisa_dg1022_user.py
#
############################################################################

import visa
import time, sys, re
import numpy as np

vendor_id   = None
device_id   = None
instr_model = None 
resources   = None
instr       = None

###############################################################
freq   = 50    # in Hz
volt   = 5.0   # Volt peak-to-peak
offset = 0.0   # Volt offset

############################################################################
visa_driver = ''  #  use either 'visa64' or 'visa32' or '@py' or left empty. 
resources = visa.ResourceManager( visa_driver ) 
devices = resources.list_resources()

if len(devices) > 0:
    print ('Found #devices: %d' % len(devices) )
    for device in devices:
        print ('>>', device)
        device = device.replace('::',',')
        fields = device.split(',')
        if len(fields) == 5 and fields[3].startswith('DG'):
            vendor_id = fields[1]
            device_id = fields[2]
            instr_model = fields[3]      
            print (vendor_id, device_id, instr_model)

print (30*'-')

############################################################################

def listInstruments():
    global resources
    devices = resources.list_resources()
    print (devices)

def selectInstrument( vendor_id, device_id, instr_model ):
    cmd_str = "USB0::%s::%s::%s::INSTR" % (vendor_id,device_id,instr_model)
    instr = resources.open_resource( cmd_str, timeout=500, chunk_size=102400 )
    return instr

def cmdWrite(cmd, dly=0.1):
    global instr
    instr.write( cmd )
    time.sleep( dly )

def cmdRead(cmd, dly=0.1):
    global instr
    instr.write( cmd )
    time.sleep( dly )
    try:
        str = instr.read()
    except Exception:
        str = None
    return str

def showInstrumentInfo():
    print ( cmdRead("*IDN?") )

############################################################################

# select Rigol DG1022
if vendor_id == '0x1AB1' and device_id == '0x0588':
    instr = selectInstrument( vendor_id, device_id, instr_model)
else:
    print ('No DG1022 instrument found !!!')
    sys.exit(-1)

showInstrumentInfo()

# connect to the remote instrument
cmdWrite( "SYSTem:REMote" )

# reset the instrument
#cmdWrite( "*RST", 1.0 )

###############################################################
def gen_data_sin():
    N = 512               # number of samples per a half period
    x = np.arange(-N,N)   # 2N points per period
    y = [ int(8191 * np.sin( np.pi*i/N) + 8192) for i in x ]
    return ','.join(map(str,y))

def gen_data_sinc():
    N = 512               # number of samples per a half period
    k = 2                 # time compression factor
    x = np.arange(-N,N)   # 2N points per period
    y = [ int(8191 * np.sinc(np.pi*k*i/N) + 8192) for i in x ]
    return ','.join(map(str,y))

def gen_data_exp_cos_sym():
    N = 256               # number of samples per a half period
    k = 4.0               # time compression factor
    x = np.arange(-N,N)   # 2N points per period
    y = [ int(8191 * np.exp(-np.abs(k*i)/N) * np.cos(np.pi*k*i/N) + 8192) 
            for i in x ]
    return ','.join(map(str,y))

###############################################################
data = gen_data_sin() 
#data = gen_data_sinc()
#data = gen_data_exp_cos_sym()

print ('turn off output CH1 1')
cmdWrite( "OUTP OFF" )

print ("select User-defined waveform")
cmdWrite( "FUNC USER" )

print ( 'max. volatile memory depth: ' + cmdRead("DATA:ATTR:POIN? VOLATILE") )

print ("set frequency: {:d} Hz".format(freq))
cmdWrite( "FREQ %d" % freq )

print ("select voltage output unit: voltage peak-to-peak")
cmdWrite( "VOLT:UNIT VPP" )

print ("set initial voltage value: {:.3f}".format( volt ))
cmdWrite( "VOLT %.1f" % volt )

print ("set initial voltage offset: {:.3f}".format( offset ))
cmdWrite( "VOLT:OFFS %.3f" % offset )

cmdWrite( "DATA:DELelete VOLATILE" )
time.sleep(1.0)

cmdWrite( "DATA:DAC VOLATILE,%s" % data ) # upload data to the volatile memory
time.sleep(1.0)

cmdWrite( "FUNC:USER VOLATILE" ) # use the data in the volatile memory
time.sleep(1.0)

print ("turn on the output CH 1")
cmdWrite("OUTP ON")
time.sleep(1.0)

print ('Done....')
sys.exit(0)

############################################################################
