#!/usr/bin/env python
# coding: utf-8

# In[2]:


from __future__ import print_function
import time
import numpy as np
import zhinst.utils
#import matplotlib.pyplot as plt


device_id = 'dev4562' # replace with your device SN here
apilevel_example = 6
err_msg = "This example only supports instruments with IA option."
(daq, device, _) = zhinst.utils.create_api_session(device_id, apilevel_example,
                                                       required_options=['IA'],
                                                       required_err_msg=err_msg)
zhinst.utils.api_server_version_check(daq)
zhinst.utils.disable_everything(daq, device)

osc_index = 0
imp_index = 0
exp_settings = [['/%s/imps/%d/enable' % (device, imp_index), 1],
                    ['/%s/imps/%d/mode' % (device, imp_index), 0],
                    ['/%s/imps/%d/auto/output' % (device, imp_index), 1],
                    ['/%s/imps/%d/auto/bw' % (device, imp_index), 1],
                    ['/%s/imps/%d/bias/enable' % (device, imp_index), 0],#no bias
                    ['/%s/imps/%d/bias/value' % (device, imp_index), 0],
                    ['/%s/imps/%d/freq' % (device, imp_index), 1000],
                    ['/%s/imps/%d/auto/inputrange' % (device, imp_index), 1],
                    ['/%s/imps/%d/output/amplitude' % (device, imp_index), 1],
                    ['/%s/imps/%d/output/range'% (device, imp_index), 1],
                    ['/%s/imps/%d/model'% (device, imp_index), 0],
                    ['/%s/sigins/%d/model'% (device, osc_index), 0.5]]  #note: this 0.5V/V scaling factor is from MUX at 1MOhm input impedance

# Subscribe to the impedance sample node path.
path = '/%s/imps/%d/sample' % (device, imp_index)
daq.set(exp_settings)
daq.sync()

n_DUT = 2

sweeper = daq.sweep()
sweeper.set('device', device)
sweeper.set('historylength', 100)
sweeper.set('gridnode', 'oscs/%d/freq' % osc_index)
sweeper.set('start', 1e3)
sweeper.set('stop', 5e6)
sweeper.set('samplecount', 100)
sweeper.set('xmapping', 1) #log spacing
sweeper.set('bandwidthcontrol', 2) #0=maunal, 1=fixed, 2=auto
sweeper.set('scan', 0) #forward
sweeper.set('loopcount', 1) #only 1 sweep for each DUT
sweeper.set('bandwidth', 10) # default standard impedance sweep settings
sweeper.set('order', 8)
sweeper.set('settling/inaccuracy', 0.01)
sweeper.set('settling/time', 0)
sweeper.set('averaging/tc', 15)
sweeper.set('averaging/sample', 20)
sweeper.set('averaging/time', 0.1)
sweeper.set('maxbandwidth', 100)
sweeper.set('bandwidthoverlap', 1)
sweeper.set('omegasuppression', 80)
sweeper.set('phaseunwrap', 0)
sweeper.set('sincfilter', 0)
sweeper.set('awgcontrol', 0)


daq.setInt('/%s/dios/0/drive' % device, 3) 
#enable bus 0 and bus 1 (8bit each) lines as output
daq.setInt('/%s/dios/0/output' % device, 4081) 
#this number is in decimal. in HEX is FF1 and in Bin is 00001111 11110001, 
#meanning all channels are switched to 1MOhm input impedance and open Mux2In2 and Mux1in1, to measure V on DUT1
daq.sync()


print("Will perform", n_DUT, "sweeps...")
timeout = 60  # [s]

def muxsweep(n):
    sweeper.subscribe(path)
    sweeper.execute()
    start = time.time()
    print("DUT",n)
    while not sweeper.finished():  # Wait until the sweep is complete, with timeout.
        time.sleep(0.2)
        progress = sweeper.progress()
        print("Individual sweep progress: {:.2%}.".format(progress[0]), end="\r")
        if (time.time() - start) > timeout:
            print("\nSweep still not finished, forcing finish...")
        #sweeper.finish()
    print("")

    sweeper.set('save/filename', 'DUT'+str(n))
    sweeper.set('save/fileformat', 4)
    print("About to save")
    sweeper.set('save/save', 1)
    print("Save started")
    save_done = sweeper.getInt('save/save')
    while save_done != 0:
        time.sleep(1)
        save_done = sweeper.getInt('save/save')
    print("Save done")
    return_flat_dict = True
    data = sweeper.read(return_flat_dict)
    sweeper.unsubscribe(path)

    return data


muxsweep(1)
daq.setInt('/%s/dios/0/output' % device, 4093) # this is Mux2In4 and Mux1in3, to measure V on DUT2
daq.sync()
muxsweep(2)


# In[ ]:




