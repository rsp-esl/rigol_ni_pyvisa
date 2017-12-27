#!/usr/bin/env python3

import visa
import time, sys
import math

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
TOO_LARGE_VALUE = (1e+37)

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

freq = 10.0; vpp = 5.0; offset = 0.0  # the properties of sine wave
cmdWrite( dg, "VOLT:UNIT VPP" )       # use voltage peak-to-peak
cmdWrite( dg, "APPL:SIN {:.3e},{:.3e},{:.3e}".format(freq,vpp,offset) )
cmdWrite( dg, "PHAS 0" )              # set phase offset to 0.0
cmdWrite( dg, "OUTP ON" )             # enable CH1 outout

############################################################################
cmdWrite( ds, ":SYST:REM" )
cmdWrite( ds, ":RUN" )
cmdWrite( ds, ":MEAS:CLE ALL" )
cmdWrite( ds, ":TIM:MAIN:SCAL {:.3e}".format( 0.01 ) )
cmdWrite( ds, ":TRIG:EDG:SOUR CHAN{:d}".format( 1 ) )
cmdWrite( ds, ":TRIG:MODE EDGE" )
cmdWrite( ds, ":TRIG:SWE AUTO" )
cmdWrite( ds, ":TRIG:EDG:LEV {:.3e}".format(0.0) )
cmdWrite( ds, ":ACQ:TYP AVER" )
cmdWrite( ds, ":ACQ:AVER 8" )        # average 8 points

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

time.sleep(1.0)

def read_vpp( channel ):
    global ds
    resp = cmdRead( ds, ":MEAS:VPP? CHAN{:d}".format( channel ), 0.2 )
    vpp = float(resp)
    if vpp > TOO_LARGE_VALUE:
        return None
    else:
        return vpp

def read_freq( channel ):
    global ds
    resp = cmdRead( ds, ":MEAS:FREQ? CHAN{:d}".format( channel ), 0.2 )
    freq = float(resp)
    if freq > TOO_LARGE_VALUE:
        return None
    else:
        return freq

def read_phase_diff():
    global ds
    resp = cmdRead( ds,":MEAS:RPH? CHAN1,CHAN2", 0.2 )
    phase_diff = float( resp )
    if phase_diff > TOO_LARGE_VALUE:
        return None
    else:
        return phase_diff

print (50*'-')

scale = 1.0

for freq in [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]:
    cmdWrite( dg, "FREQ {:.3e}".format(freq) )
    time.sleep(1.0)
    cmdWrite( ds, ":TIM:SCAL {:.3e}".format( 0.5/freq ) )
    if freq < 10:
       time.sleep(5.0)
    else:
       time.sleep(3.0)

    while True:
        freq = read_freq(1)
        if freq != None:
            break
        print ('.')
        time.sleep(0.5)

    vpp2 = read_vpp(2)
    if vpp2 < 0.5:
        scale = 0.1
    elif vpp2 < 0.2:
        scale = 0.05
    elif vpp2 < 0.1:
        scale = 0.02

    cmdWrite( ds, ":CHAN{:d}:SCAL {:.3e}".format( 2, scale ) )
    time.sleep(2.0)

    vpp2 = read_vpp(2); vpp1 = read_vpp(1);
    if vpp2 < 0.100:
        break

    phase = None
    while True:
        phase = read_phase_diff()
        if phase != None:
            break
        print ('.')
        time.sleep(0.5)

    str = "Freq(Hz): {:.1f}, Vpp2/Vpp1: {:.3f}, Phase(Deg.): {:.1f}"
    print ( str.format(freq, vpp2/vpp1, -phase) )

    print (50*'-')

resources.close()
del resources
dg.close()
del dg
ds.close()
del ds

sys.exit(0)

############################################################################