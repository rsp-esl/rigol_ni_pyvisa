#!/usr/bin/env python

import visa
import time, sys

############################################################################
# Date: 2017-11-18
############################################################################
# Author: Rawat S. 
#   (Dept. of Electrical & Computer Engineering, KMUTNB, Bangkok/Thailand)
#
############################################################################
# Description:
#    This Python script shows how to connect to a Rigol digital oscilloscope,
#    DS1000 Series (tested with DS1052E). It captures the waveform data
#    on channel 1 and visualizes the data using matplotlib.
#    Note that the number of data points to be read will be to the max. value
#    which is 16384 (instead of 600.).
#
############################################################################

import visa
import time, sys
import numpy as np 
import matplotlib.pyplot as plot

DS1052E_ID  = '0x0588'
INSTR_ID    = DS1052E_ID 

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
        if len(fields) == 5 and fields[3].startswith('DS'):
            vendor_id = fields[1]
            device_id = fields[2]
            instr_model = fields[3]      
            print (vendor_id, device_id, instr_model)

############################################################################

def listInstruments():
    global resources
    devices = resources.list_resources()
    print (devices)

def selectInstrument( vendor_id, device_id, instr_model ):
    cmd_str = "USB0::%s::%s::%s::INSTR" % (vendor_id,device_id,instr_model)
    instr = resources.open_resource( cmd_str, timeout=100, chunk_size=1024000 )
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
print ('-'*60)

if vendor_id == '0x1AB1' and device_id == INSTR_ID:
    instr = selectInstrument( vendor_id, device_id, instr_model)
else:
    print ( 'No Rigol oscilloscope instrument found !!!' )
    sys.exit(-1)

showInstrumentInfo()

# connect to the remote instrument
cmdWrite( "SYSTem:REMote" )  # change from LOCAL to REMOTE 

############################################################################
cmdWrite( ":RUN" )      # enter run mode

# Oscilloscope Settings 
time_per_div = 0.005  # for example, use 0.01, 0.02, 0.05, 0.001, 0.002
cmdWrite(':TIM:SCAL %f' % time_per_div )  # set timescale (seconds)
cmdWrite(':CHAN2:DISP OFF')  # CH2: turn off display
cmdWrite(":CHAN1:COUP DC")   # CH1: use DC coupling 
cmdWrite(':CHAN1:DISP ON')   # CH1: turn on display 
cmdWrite(':CHAN1:SCAL 1.0')  # CH1: set vertical scale to 1.0 V
cmdWrite(':CHAN1:OFFS 0.0')  # CH1: set vertical offset to 0.0 V

time.sleep(1.0)
cmdWrite(":STOP")
time.sleep(1.0)

############################################################################
print ('-'*60)

# get the sampling rate
sampling_rate = float(cmdRead(':ACQ:SAMP?',0.5).strip())
print ('Sampling rate: {:.3f} MHz'.format( sampling_rate*10e-6 ) )

# Retrieve oscilloscope settings 
time_per_div    = float(cmdRead(":TIM:SCAL?",0.5).strip())
time_offset     = float(cmdRead(":TIM:OFFS?").strip())
volt_per_div    = float(cmdRead(":CHAN1:SCAL?").strip())
vertical_offset = float(cmdRead(":CHAN1:OFFS?").strip())

print ( 'Timescale:', time_per_div )
print ( 'Time Offset:', time_offset )
print ( 'Volt/Div Ch1:', volt_per_div )
print ( 'Vertical Offset Ch1:', vertical_offset )

cmdWrite(":WAV:MODE RAW")   # set waveform mode to RAW
cmdWrite(":WAV:FORM BYTE") 
cmdWrite(":WAV:POIN:MODE MAX")  
cmdWrite(":WAV:SOUR CHAN1") # select channel 1 as source
cmdWrite(":WAV:STAR 1")     # set start address for waveform data reading
cmdWrite(":WAV:RES")        # reset waveform reading
cmdWrite(":WAV:BEG")        # start waveform reading

############################################################################
print ('-'*60)

# get waveform data for channel 1
rawdata = cmdReadRaw(":WAV:DATA? CHAN1",0.5)     

cmdWrite(":RUN")
cmdWrite(":KEY:FORCE",0.5)
instr.close()

############################################################################

bytes_len = int( rawdata[2:10] ) # get the number of data points
print ('retrieve %d bytes' % bytes_len)
rawdata = rawdata[10:] # skip the first 10 bytes 
data = np.frombuffer(rawdata, 'B' )

data = ((240 - data) * (volt_per_div/25))
data = data - (vertical_offset + volt_per_div * 4.6)
data_len = len(data)

time_per_div = 1.0/sampling_rate

t_left  = time_offset - (data_len/2)/sampling_rate
t_right = time_offset + (data_len/2)/sampling_rate

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
plot.title( "Rigol: Waveform Capture - Channel 1" )
plot.ylabel( "Voltage [V]" )
plot.xlabel( "Time [%s]" % ts_unit )
plot.xlim( ts[0], ts[-1] )
plot.grid(True)
plot.savefig( 'rigol_plot.png',dpi=200,bbox_inches='tight' )
plot.show()

############################################################################
# References:
# - http://www.righto.com/2013/07/rigol-oscilloscope-hacks-with-python.html
# - https://rigol.desk.com/customer/en/portal/articles/2269119-how-do-i-format-the-data-returned-from-a-ds1000e-d-series-scope-
############################################################################
