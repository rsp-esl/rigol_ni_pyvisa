#!/usr/bin/env python

###############################################################
# Date: 2017-Nov-11
# Rigol Instrument tested: RIGOL DG1022 
#  Generate a sinusoidal waveform with different frequencies..
###############################################################
#
# 1) install pyusb
#
#   $ pip install pyusb -U
#
# 2) install pyVISA
#
#   $ pip install pyvisa -U
#
###############################################################

import visa
import time, sys

instr = None

resources = visa.ResourceManager('visa32')
devices = resources.list_resources()
print devices

def listInstruments():
    global resources
    devices = resources.list_resources()
    print devices

def selectInstrument( vendor_id, device_id ):
    cmd_str = "USB0::%s::%s::DG1D131101556::INSTR" % (str(vendor_id),str(device_id))
    instr = resources.open_resource( cmd_str )
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
    print cmdRead("*IDN?")

# select Rigol DG1022
instr = selectInstrument( 0x1ab1, 0x0588 )

showInstrumentInfo()
# sample output: RIGOL TECHNOLOGIES,DG1022 ,DG1D131101556,,00.02.00.06.00.02.07

# connect to the remote instrument
cmdWrite( "SYSTem:REMote" )

# reset the instrument
cmdWrite( "*RST", 1.0 )

###############################################################
freq   = 100
volt   = 1
offset = 0
phase  = 0
###############################################################

print 'turn off output CH1 1'
cmdWrite( "OUTP1 OFF" )

print "select Sine waveform"
cmdWrite( "FUNC SIN" )

print "set initial frequency: {:d} Hz".format(freq)
cmdWrite( "FREQ %d" % freq )

print "select voltage output unit: voltage peak-to-peak"
cmdWrite( "VOLT:UNIT VPP" )

print "set initial voltage value: {:.3f}".format( volt )
cmdWrite( "VOLT %.1f" % volt )

print "set initial voltage offset: {:d}".format( offset )
cmdWrite("VOLT:OFFS %.3f" % offset )

print "set initial phase: {:d} [Deg.]".format( phase )
cmdWrite( "PHAS %d" % phase )

print "turn on the output CH 1"
cmdWrite("OUTP1 ON")

try:
    volt = 2.0
    for freq in [100,200,500,1000,2000,5000,10000]:
        cmdWrite("APPL:SIN {:d},{:.3f},{:.3f}".format(freq, volt, offset) )
        print 'Freq:      {:6.1f} Hz'.format( float(cmdRead( "FREQ?" )) )
        print 'VOLT:LOW:  {:+2.1f} V'.format( float( cmdRead( "VOLT:LOW?" )) )
        print 'VOLT:HIGH: {:+2.1f} V'.format( float( cmdRead( "VOLT:HIGH?" )) )
        print 40*'-'
        time.sleep(2.0)

except KeyboardInterrupt:
    print 'Teriminate....'

print 'Done....'

###############################################################
