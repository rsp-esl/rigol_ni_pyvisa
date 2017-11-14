#!/usr/bin/env python

import visa
import time, sys

############################################################################
# Date: 2017-11-14
############################################################################
# Author: Rawat S. 
#   (Dept. of Electrical & Computer Engineering, KMUTNB, Bangkok/Thailand)
#
############################################################################
# Short Description:
#   This Python script is used to demonstrate how to program 
#   the Rigol DS1054z / DS2072A digital oscilloscope via USB.
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
#   $ python2  ./test_pyvisa_ds1054z.py
#   $ python3  ./test_pyvisa_ds1054z.py
#
############################################################################

import visa
import time, sys

# select Rigol DS1054z : 0x04CE
# select Rigol DS2072A : 0x04B0

DS1054Z_ID = '0x04CE'
DS2072A_ID = '0x04B0'

INSTR_ID   = DS2072A_ID 

vendor_id = None
device_id = None
instr_model = None 
resources = None
instr = None

USE_PROBE_10X = True

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
        if len(fields) == 5 and fields[3].startswith('DS'):
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
    print ( cmdRead("*IDN?") )

############################################################################

if vendor_id == '0x1AB1' and device_id == INSTR_ID:
    instr = selectInstrument( vendor_id, device_id, instr_model)
else:
    print ( 'No Rigol oscilloscope instrument found !!!' )
    sys.exit(-1)

showInstrumentInfo()

# connect to the remote instrument
cmdWrite( "SYSTem:REMote" )  # change from LOCAL to REMOTE 

#cmdWrite( "*RST", 1.0 )      # reset the instrument
cmdWrite( ":STOP" )          # stop the instrument (enter STOP state)

############################################################################

print ( 'Send parameters to the instrument...' )
cmdWrite( ":RUN",1.0 )
cmdWrite( ":SYST:AUT ON", 1.0 )

# clear all measurements
cmdWrite( ":MEAS:CLE ALL", 0.2 )

# enable frequency measurement on CH1
cmdWrite( ":MEAS:FREQ CHAN1", 0.2 )
# enable frequency measurement on CH2
cmdWrite( ":MEAS:FREQ CHAN2", 0.2 )

# enable period measurement on CH1
cmdWrite( ":MEAS:PER CHAN1", 0.2 )
# enable period measurement on CH2
cmdWrite( ":MEAS:PER CHAN2", 0.2 )

# set PSA=CH1 and PSB=CH2
cmdWrite( ":MEAS:SET:PSA CHAN1", 0.2 )
cmdWrite( ":MEAS:SET:PSB CHAN2", 0.2 )

if USE_PROBE_10X:
    print ('Use probe 10x .... Please check your probe setting !!!')
    cmdWrite( ":CHAN1:PROB 10", 0.2 )     # CH1 10x probe
    cmdWrite( ":CHAN2:PROB 10", 0.2 )     # CH2 10x probe
else:
    print ('Use probe  1x .... Please check your probe setting !!!')
    cmdWrite( ":CHAN1:PROB 1", 0.2 )     # CH1 1x probe
    cmdWrite( ":CHAN2:PROB 1", 0.2 )     # CH2 1x probe

cmdWrite( ":CHAN1:DISP 1", 0.2 )     # turn on CH1 display
cmdWrite( ":CHAN2:DISP 1", 0.2 )     # turn on CH2 display
cmdWrite( ":CHAN1:COUP DC", 0.2 )    # CH1 DC coupling
cmdWrite( ":CHAN2:COUP DC", 0.2 )    # CH2 DC coupling
cmdWrite( ":CHAN1:SCAL 0.5", 0.2 )   # CH1 scale 0.1 V/div
cmdWrite( ":CHAN2:SCAL 0.5", 0.2 )   # CH2 scale 0.1 V/div
cmdWrite( ":CHAN1:OFFS 0.0", 0.2 )   # CH1 offset 0.0 V
cmdWrite( ":CHAN2:OFFS 0.0", 0.2 )   # CH2 offset 0.0 V

cmdWrite( ":TRIG:EDG:SOUR CHAN1", 0.2 ) # trigger source = CH1
cmdWrite( ":TRIG:MODE EDGE", 0.2 )      # trigger mode   = EDGE
cmdWrite( ":TRIG:SWE AUTO", 0.2 )       # trigger sweep  = AUTO
cmdWrite( ":TRIG:EDG:LEV 0.0", 0.2 )    # trigger level  = 0.0 V

# step: (1 2 5) * 10^x
# e.g. 10 20 50 100 200 500 1000 2000 5000 ...
cmdWrite( ":TIM:SCAL 0.000100", 0.5 )     # timebase scale = 100 usec/div

# Note: invalid return value: 9.9E37

print ('Start reading from the instrument...')
print (40*'-')

TOO_LARGE_VALUE = (1e+37)

try:
    # for each iteration, a different value of time-div scale is used.
    time_div_scales = [20, 50, 100, 200, 500, 1000, 2000] # in usec (microseconds)
    
    for i in range( len(time_div_scales) ): 

        time_div = time_div_scales[i] 
        cmdWrite( ":TIM:SCAL %.6f" % (time_div*1e-6), 0.5 ) 
        print ("time scale: %.6f" % (time_div*1e-6))

        ######################################################
        # Measure frequency on Channel 1 (Channel A)
        ######################################################

        resp = cmdRead( ":MEAS:FREQ? CHAN1", 0.1 )[:-1]
        #print ('resp: [%s]' % resp)
        freq1 = float(resp)
        if freq1 > TOO_LARGE_VALUE:
            print ( "CH1 Freq: ---- Hz" )
        else:
            print ( "CH1 Freq: {:.3f} Hz".format( freq1 ) )

        ######################################################
        # Measure frequency on Channel 2 (Channel B)
        ######################################################

        resp = cmdRead( ":MEAS:FREQ? CHAN2", 0.1 )[:-1]
        #print 'resp: [%s]' % resp
        freq2 = float(resp)
        if freq2 > TOO_LARGE_VALUE:
            print ( "CH2 Freq: ---- Hz" )
        else:
            print ( "CH2 Freq: {:.3f} Hz".format( freq2 ) )

        ######################################################
        # Measure period on Channel 1 (Channel A)
        ######################################################

        resp = cmdRead( ":MEAS:PER? CHAN1", 0.1 )[:-1]
        #print ('resp: [%s]' % resp)
        period1 = float(resp)
        if period1 > TOO_LARGE_VALUE:
            print ( "CH1 Period: ---- msec" )
        else:
            print ( "CH1 Period: {:.3f} msec".format( 1000*period1 ) )

        ######################################################
        # Measure period on Channel 2 (Channel B)
        ######################################################

        resp = cmdRead( ":MEAS:PER? CHAN2", 0.1 )[:-1]
        #print ('resp: [%s]' % resp)
        period2 = float(resp)
        if period2 > TOO_LARGE_VALUE:
            print ( "CH2 Period: ---- msec" )
        else:
            print ( "CH2 Period: {:.3f} msec".format( 1000*period2 ) )

        ######################################################
        # Measure Voltage Peak-to-Peak on Channel 1 (Channel A)
        ######################################################

        # enable Vpp measurement on CH1
        cmdWrite( ":MEAS:VPP CHAN1", 0.5 )
        resp = cmdRead( ":MEAS:VPP:SAV? CHAN1", 0.2 )[:-1] # get average value on CH1
        #print ('resp: [%s]' % resp)
        vpp1 = float(resp)
        if vpp1 > TOO_LARGE_VALUE:
            print ( "CH1 Vpp(avg): ---- V" )
        else:
            print ( "CH1 Vpp(avg): {:.3f} V".format( vpp1 ) )

        ######################################################
        # Measure Voltage Peak-to-Peak on Channel 2 (Channel B)
        ######################################################

        # enable Vpp measurement on CH2
        cmdWrite( ":MEAS:VPP CHAN2", 0.5 )
        resp = cmdRead( ":MEAS:VPP:SAV? CHAN2", 0.2 )[:-1] # get average value on CH2
        #print ('resp: [%s]' % resp)
        vpp2 = float(resp)
        if vpp2 > 1e+37:
            print ( "CH2 Vpp(avg): ---- V" )
        else:
            print ( "CH2 Vpp(avg): {:.3f} V".format( vpp2 ) )

        ######################################################
        # Measure Delay between the falling edge of Channel 1 
        # and the falling edge of Channel 2
        ######################################################

        # enable measurement of delay (falling-edge to falling edge)
        cmdWrite( ":MEAS:FDEL CHAN1,CHAN2", 0.5 )
        resp = cmdRead( ":MEAS:FDEL:SAV?", 0.2 )[:-1]
        #print ('resp: [%s]' % resp.strip())
        d1to2 = float(resp)
        if d1to2 > TOO_LARGE_VALUE:
            print ( "Delay CH1->CH2: ---- usec" )
        else:
            print ( "Delay CH1->CH2: {:.3f} msec".format( 1000*d1to2 ) )
        print (40*'-','\n')

        time.sleep(4.0)

except KeyboardInterrupt:
        print ( 'Terminated...' )

if instr != None:
    instr.close()
print ( 'Done...' )
time.sleep(1.0)
sys.exit(0)

############################################################################
