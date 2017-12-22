#!/usr/bin/env python

############################################################################
# Date: 2017-11-16
############################################################################
# Author: Rawat S.
#   (Dept. of Electrical & Computer Engineering, KMUTNB, Bangkok/Thailand)
############################################################################

import visa
import time, sys, re
import numpy as np

vendor_id   = None
device_id   = None
instr_model = None
resources   = None
instr       = None

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
        if len(fields) >= 5 and fields[3].startswith('DG'):
            vendor_id = fields[1]
            device_id = fields[2]
            if not vendor_id.startswith('0x'):
                vendor_id = '0x{:04X}'.format( int(fields[1]) )
            if not device_id.startswith('0x'):
                device_id = '0x{:04X}'.format( int(fields[2]) )
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
    print ( cmdRead("*IDN?",1.0) )

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

############################################################################
def gen_data_sin():
    N = 512                   # number of samples per period
    x = np.arange(-N/2,N/2)   # N points per period
    #y = [ int(8191 * np.sin( 2*np.pi*i/N) + 8192) for i in x ]
    y = 8191*np.sin(2*x*np.pi/N) + 8192
    y = y.astype(int)
    return ','.join(map(str,y))

def gen_data_halfwave_sin():
    N = 512                   # number of samples per period
    x = np.arange(-N/2,N/2)   # N points per period
    #y = [ int(8191 * np.abs(np.sin( np.pi*i/N)) + 8192) for i in x ]
    y = 8191*np.abs(np.sin(x*np.pi/N)) + 8192
    y = y.astype(int)
    return ','.join(map(str,y))

def gen_data_square( duty_cycle = 0.5 ):
    N = 1024              # number of samples per period
    x = np.arange(0,N)    # N points per period
    y = [ int(16383 * (i < duty_cycle*N)) for i in x ]
    return ','.join(map(str,y))

def gen_data_sawtooth( ):
    N = 2048              # number of samples per period
    x = np.arange(0,N)    # N points per period
    y = [ int( 16383.0*i/N ) for i in x ]
    return ','.join(map(str,y))

#data = gen_data_sin()
#data = gen_data_halfwave_sin()
#data = gen_data_square(0.25)
data = gen_data_sawtooth()

############################################################################
freq   = 1000    # in Hz
volt   = 5.0     # Volt peak-to-peak
offset = 0.0     # Volt offset

print ('turn off output CH1')
cmdWrite( "OUTP OFF" )

print ("select user-defined (arbitrary) waveform")
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
time.sleep(1.5)

cmdWrite( "FUNC:USER VOLATILE" ) # apply the data in the volatile memory
time.sleep(1.0)

print ("turn on the output CH1")
cmdWrite("OUTP ON")
time.sleep(1.0)

if instr != None:
    instr.close()
    del instr
if resources != None:
    resources.close()
    del resources

print ('Done....')
sys.exit(0)
############################################################################
