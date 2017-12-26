#!/usr/bin/env python3

import visa
import time, sys

############################################################################
# Date: 2017-12-26
############################################################################
# Author: Rawat S.
#   (Dept. of Electrical & Computer Engineering, KMUTNB, Bangkok/Thailand)
#
############################################################################

ds = None  # digital oscilloscope (DS2072A)
dg = None  # digital function generator (DG1022)

USE_PROBE_10X = True
TOO_LARGE_VALUE = (9e+37)

############################################################################
def cmdWrite(instr, cmd, dly=0.1):
    instr.write( cmd )
    time.sleep( dly )

def cmdRead(instr, cmd, dly=0.1):
    instr.write( cmd )
    time.sleep( dly )
    try:
        str = instr.read()
    except Exception:
        str = None
    return str[:-1]

############################################################################
visa_driver = '@py'  # use 'visa64', 'visa32' (Windows) or '@py' (Linux)
resources = visa.ResourceManager( visa_driver )
devices   = resources.list_resources()

if len(devices) > 0:
    print ('Found #devices: %d' % len(devices) )
    for device in devices:
        print ('>>', device)
        device = device.replace('::',',')
        fields = device.split(',')

        if len(fields) >= 5:
            vendor_id = fields[1]
            device_id = fields[2]
            if not vendor_id.startswith('0x'):
                vendor_id = '0x{:04X}'.format( int(fields[1]) )
            if not device_id.startswith('0x'):
                device_id = '0x{:04X}'.format( int(fields[2]) )
            instr_model = fields[3]
            cmd_str = "USB?::%s::%s::%s::INSTR" % (vendor_id,device_id,instr_model)

            if instr_model.startswith('DS'):
                ds = resources.open_resource( cmd_str, timeout=500, chunk_size=102400 )
            elif instr_model.startswith('DG'):
                dg = resources.open_resource( cmd_str, timeout=500, chunk_size=102400 )

if ds == None:
    print ('Rigol digital oscilloscope not found !!!' )
    sys.exit(-1)
else:
    print ( cmdRead(ds,"*IDN?") )

if dg == None:
    print ('Rigol digital function generator not found !!!' )
    sys.exit(-1)
else:
    print ( cmdRead(dg,"*IDN?") )

############################################################################
# connect to the function generator DG1022 and send SCPI commands
cmdWrite( dg, "SYST:REM", 1.0 )

freq = 50.0; vpp = 5.0; offset = 0.0 # the properties of sine wave
cmdWrite( dg, "VOLT:UNIT VPP" )      # use voltage peak-to-peak
cmdWrite( dg, "APPL:SIN {:.3e},{:.3e},{:.3e}".format(freq,vpp,offset) )
cmdWrite( dg, "PHAS 0" )             # set phase offset to 0.0
cmdWrite( dg, "OUTP ON" )            # enable CH1 outout

cmdWrite( dg, "VOLT:UNIT:CH2 VPP" )  # use voltage peak-to-peak
cmdWrite( dg, "APPL:SIN:CH2 {:.3e},{:.3e},{:.3e}".format(freq,vpp,offset) )
cmdWrite( dg, "PHAS:CH2 90" )        # set phase offset to 90.0
cmdWrite( dg, "OUTP:CH2 ON" )        # enable CH2 output

time.sleep( 0.5 )
cmdWrite( dg, "PHAS:ALIGN" )         # enable align phase output of dual channels

############################################################################
cmdWrite( ds, ":SYST:REM" )
cmdWrite( ds, ":RUN" )
cmdWrite( ds, ":MEAS:CLE ALL" )
cmdWrite( ds, ":TIM:MAIN:SCAL {:.3e}".format( 0.005 ) )
cmdWrite( ds, ":TRIG:EDG:SOUR CHAN{:d}".format( 1 ) )
cmdWrite( ds, ":TRIG:MODE EDGE" )
cmdWrite( ds, ":TRIG:SWE AUTO" )
cmdWrite( ds, ":TRIG:EDG:LEV {:.3e}".format(0.0) )
cmdWrite( ds, ":ACQ:TYP AVER" )
cmdWrite( ds, ":ACQ:AVER 16" )       # average 16 points

for chan in range(1,3):
    print ("Setting configurations for CHAN{:d}".format( chan ) )
    if USE_PROBE_10X:
        cmdWrite( ds,":CHAN{:d}:PROB 10".format( chan ) )
    else:
        cmdWrite( ds,":CHAN{:d}:PROB 1".format( chan )  )
    cmdWrite( ds, ":CHAN{:d}:DISP 1".format( chan ) )
    cmdWrite( ds, ":CHAN{:d}:COUP AC".format( chan )  )
    cmdWrite( ds, ":CHAN{:d}:SCAL {:.3e}".format( chan, 1.0 ) )
    cmdWrite( ds, ":CHAN{:d}:OFFS {:.3e}".format( chan, 0.0 ) )
    cmdWrite( ds, ":MEAS:FREQ CHAN{:d}".format( chan ) )
    cmdWrite( ds, ":MEAS:PER CHAN{:d}".format( chan ) )
    cmdWrite( ds, ":MEAS:VPP CHAN{:d}".format( chan ) )

# set PSA=CHAN1 and PSB=CHAN2 for phase and delay measurement
cmdWrite( ds, ":MEAS:SET:PSA CHAN1" )
cmdWrite( ds, ":MEAS:SET:PSB CHAN2" )

# enable measurement of phase difference (rising-edge to rising-edge)
cmdWrite( ds, ":MEAS:RPH CHAN1,CHAN2" )

time.sleep(1.0)

def read_vpp( channel ):
    resp = cmdRead( ds, ":MEAS:VPP? CHAN{:d}".format( channel ), 0.2 )
    vpp = float(resp)
    if vpp > TOO_LARGE_VALUE:
        print ( "CHAN{:d} Vpp: ---- V".format( channel) )
    else:
        print ( "CHAN{:d} Vpp: {:.3f} V".format( channel, vpp ) )

def read_freq( channel ):
    resp = cmdRead( ds, ":MEAS:FREQ? CHAN{:d}".format( channel ), 0.2 )
    freq = float(resp)
    if freq > TOO_LARGE_VALUE:
        print ( "CHAN{:d} Freq: ---- Hz".format( channel ) )
    else:
        print ( "CHAN{:d} Freq: {:.1f} Hz".format( channel, freq ) )

def read_phase_diff():
    resp = cmdRead( ds,":MEAS:RPH? CHAN1,CHAN2", 0.2 )
    phase_delay = float( resp )
    if phase_delay > TOO_LARGE_VALUE:
        print ( "Cannot measure the phase difference" )
    else:
        print ( "Phase difference CHAN1->CHAN2: {:.1f} deg.".format( phase_delay) )

# perform the measurements 3 times
print (50*'-')
for i in range(3):
    read_vpp(1)
    read_vpp(2)
    read_freq(1)
    read_freq(2)
    read_phase_diff()
    print (50*'-')

resources.close()
del resources
dg.close()
del dg
ds.close()
del ds

sys.exit(0)
############################################################################
