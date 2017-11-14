#!/usr/bin/env python

#!/usr/bin/env python

############################################################################
# Date: 2017-11-14
############################################################################
# Author: Rawat S. 
#   (Dept. of Electrical & Computer Engineering, KMUTNB, Bangkok/Thailand)
#
############################################################################
# Short Description:
#   This Python script is used to demonstrate how to program 
#   the Rigol DG1022 function generator via USB. It will command the
#   instrument to generate a sinusoidal waveform with different frequencies.
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
#   $ python2  ./test_pyvisa_dg1022.py
#   $ python3  ./test_pyvisa_dg1022.py
#
############################################################################

import visa
import time, sys, re

vendor_id = None
device_id = None
instr_model = None 
resources = None
instr = None

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
        if len(fields) == 5:
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
    print (cmdRead("*IDN?"))

############################################################################

# select Rigol DG1022
if vendor_id == '0x1AB1' and device_id == '0x0588':
    instr = selectInstrument( vendor_id, device_id, instr_model)
else:
    print ('No DG1022 instrument found !!!')
    sys.exit(-1)

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

print ('turn off output CH1 1')
cmdWrite( "OUTP1 OFF" )

print ("select Sine waveform")
cmdWrite( "FUNC SIN" )

print ("set initial frequency: {:d} Hz".format(freq))
cmdWrite( "FREQ %d" % freq )

print ("select voltage output unit: voltage peak-to-peak")
cmdWrite( "VOLT:UNIT VPP" )

print ("set initial voltage value: {:.3f}".format( volt ))
cmdWrite( "VOLT %.1f" % volt )

print ("set initial voltage offset: {:d}".format( offset ))
cmdWrite("VOLT:OFFS %.3f" % offset )

print ("set initial phase: {:d} [Deg.]".format( phase ))
cmdWrite( "PHAS %d" % phase )

print ("turn on the output CH 1")
cmdWrite("OUTP1 ON")

try:
    volt = 2.0
    for freq in [100,200,500,1000,2000,5000,10000]:
        cmdWrite("APPL:SIN {:d},{:.3f},{:.3f}".format(freq, volt, offset) )
        print ('Freq:      {:6.1f} Hz'.format( float(cmdRead( "FREQ?" )) ))
        print ('VOLT:LOW:  {:+2.1f} V'.format( float( cmdRead( "VOLT:LOW?" )) ))
        print ('VOLT:HIGH: {:+2.1f} V'.format( float( cmdRead( "VOLT:HIGH?" )) ))
        print (40*'-')
        time.sleep(2.0)

except KeyboardInterrupt:
    print ('Teriminated....')

print ('Done....')
time.sleep(1.0)
sys.exit(0)

############################################################################
