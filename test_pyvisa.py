#!/usr/bin/env python

import visa
import time, sys

resources = visa.ResourceManager('visa64')
devices = resources.list_resources()
print devices
print 30*'-'

if len(devices) > 0:
    instr = resources.open_resource( devices[0] )
    instr.write( '*IDN?' )
    print instr.read()
else:
    print 'No devices found'

print '\nDone....'


