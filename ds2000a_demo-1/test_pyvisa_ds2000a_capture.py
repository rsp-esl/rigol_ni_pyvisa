#!/usr/bin/env python

import visa
import time, sys

############################################################################
# Date: 2017-11-20
############################################################################
# Author: Rawat S. 
#   (Dept. of Electrical & Computer Engineering, KMUTNB, Bangkok/Thailand)
#
############################################################################
#  Tested with Rigol DS2072A digital oscilloscope (firmware: 00.03.05.SP3) 
#  Read screen waveform data and visual the waveform using python-matplotlib.
#  Note that 1400 data points are read out from the oscilloscope.
############################################################################

import visa
import time, sys
import numpy as np 
import matplotlib.pyplot as plot
import io

# select Rigol DS1054z : 0x04CE
# select Rigol DS2072A : 0x04B0

DS1054Z_ID = '0x04CE'
DS2072A_ID = '0x04B0'

INSTR_ID   = DS2072A_ID 

vendor_id   = None
device_id   = None
instr_model = None 
resources   = None
instr       = None

PROBE_RATIO = 10  # use probe 1x or 10x
############################################################################

visa_driver = 'visa64'  #  use either 'visa64' or 'visa32' or '@py' or left empty. 
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
    instr = resources.open_resource( cmd_str, timeout=1000, chunk_size=1024000 )
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
    except Exception as ex:
        print (ex)
        str = None
    return str

def cmdReadRaw(cmd, dly=0.1):
    global instr
    instr.write( cmd )
    time.sleep( dly )
    try:
        data = instr.read_raw()
    except Exception as ex:
        print (ex)
        data = None
    return data

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
cmdWrite('SYSTem:REMote')  # change from LOCAL to REMOTE 

############################################################################
cmdWrite(':CHAN2:DISP OFF')

timescale = 0.005
cmdWrite(':TIM:SCAL %f' % timescale )      # timescale
cmdWrite(':TIM:OFFS 0.0' )                 # timescale offset in seconds
cmdWrite(':CHAN1:PROB %d' % PROBE_RATIO )  # Channel 1: use 10x probe
cmdWrite(':CHAN1:COUP DC')                 # Channel 1: use DC coupling
cmdWrite(':CHAN1:SCAL 1.0')                # Channel 1 vertical scale 1 volts
cmdWrite(':CHAN1:OFFS 0.0')                # Channel 1 vertical offset 0 volts
cmdWrite(':CHAN1:DISP ON')                 # Channel 1 on

cmdWrite(':RUN')
time.sleep(2.0)
cmdWrite(':STOP')

cmdWrite(':WAV:MODE NORM')   # set waveform mode
cmdWrite(':WAV:FORM BYTE') 
cmdWrite(':WAV:POIN 1400') 
cmdWrite(':WAV:SOUR CHAN1')  # select channel 1 as source
cmdWrite(':WAV:RES')         # reset waveform reading
cmdWrite(':WAV:BEG')         # start waveform reading

wave_preamble = cmdRead(':WAV:PRE?', 0.5).strip()
data_params = wave_preamble.split(',')
if len(data_params) != 10:
    print ('Reading waveform paramters error!')
    sys.exit(-1)

# format, type, points, count, xinc, xorg, xref, yinc, yor, yref
points = float(data_params[2])
xinc   = float(data_params[4]) # x increment (in seconds)
xorg   = float(data_params[5]) # x offset
xref   = float(data_params[6]) # x reference
yinc   = float(data_params[7]) # y increment
yorg   = float(data_params[8]) # y offset
yref   = float(data_params[9]) # y reference (in volts)

print('data points: %d' % points )
print( xinc, xorg, xref)
print( yinc, yorg, yref)

sampling_rate       = float(cmdRead(':ACQ:SRAT?',0.5).strip())
time_per_div        = float(cmdRead(':TIM:SCAL?',0.5).strip())
time_offset         = float(cmdRead(':TIM:OFFS?').strip())
ch1_volt_per_div    = float(cmdRead(':CHAN1:SCAL?').strip())
ch1_vertical_offset = float(cmdRead(':CHAN1:OFFS?').strip())

x_inc = float(cmdRead(':WAV:XINC?').strip())
x_ref = float(cmdRead(':WAV:XREF?').strip())
x_org = float(cmdRead(':WAV:XOR?').strip()) 

y_inc = float(cmdRead(':WAV:YINC?').strip())
y_ref = float(cmdRead(':WAV:YREF?').strip())
y_org = float(cmdRead(':WAV:YOR?').strip()) 

print ( 'Sampling Rate   : ', sampling_rate )
print ( 'Time/Div        : ', time_per_div )
print ( 'Time Offset     : ', time_offset )
print ( 'Volt/Div Ch1    : ', ch1_volt_per_div )
print ( 'Volt Offset Ch1 : ', ch1_vertical_offset )
print ( 'X increment     : ', x_inc )
print ( 'X reference     : ', x_ref )
print ( 'X offset        : ', x_org )
print ( 'Y increment     : ', y_inc )
print ( 'Y reference     : ', y_ref )
print ( 'Y offset        : ', y_org )

mem_depth = int(cmdRead(':ACQ:MDEP?',0.5).strip())
sampling_rate_mega_hz = (1e-6) * float(cmdRead(':ACQ:SRAT?',0.5).strip())

print ( 'Memory Depth : %d Points' % mem_depth )
print ( 'Sampling Rate: %.3f MHz'  % sampling_rate_mega_hz )

rawdata = cmdReadRaw( ':WAV:DATA?' )  # get waveform data

cmdWrite(':WAV:END')        # stop waveform reading
cmdWrite(':RUN') 
cmdWrite('SYST:LOC')
instr.close()

if rawdata != None:
    bytes_len = int( rawdata[2:11] ) 
    rawdata = rawdata[11:-1]
    data = np.frombuffer( rawdata,'B' )
    data = (data - yref - yorg) * yinc
else:
    print ('Read data error')
    sys.exit(-1)

data_len = len(data)
t_left   = (xref + xorg)
t_right  = (t_left + data_len * x_inc ) 
ts = np.linspace( t_left, t_right, num=data_len )

if (ts[-1] < 1e-3):
    ts = ts * 1e6
    ts_unit = "usec"
elif (ts[-1] < 1.0):
    ts = ts * 1e3
    ts_unit = "msec"
else:
    ts_unit = "sec"

plot.plot(ts, data)
plot.title( 'Rigol: Waveform Capture - CH1' )
plot.ylabel( 'Voltage [V]' )
plot.xlabel( 'Time [%s]' % ts_unit )
plot.xlim( ts[0], ts[-1] )
plot.grid(True)
plot.savefig( 'rigol_plot.png',dpi=200,bbox_inches='tight' )
plot.show()

time.sleep(1.0)
print('Done....')

############################################################################
