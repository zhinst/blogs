#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from __future__ import print_function
import time
import numpy as np
import pandas as pd 
import zhinst.utils
import matplotlib.pyplot as plt
from matplotlib import ticker, cm
import matplotlib as mpl
mpl.rcParams['text.color'] = '#009ee0'
mpl.rcParams['axes.labelcolor'] = '#009ee0'
mpl.rcParams['xtick.color'] = '#009ee0'
mpl.rcParams['ytick.color'] = '#009ee0'

device_id = 'dev4220' # replace with your device SN here
apilevel_example = 6
err_msg = "This example only supports instruments with IA option."
(daq, device, _) = zhinst.utils.create_api_session(device_id, apilevel_example,
                                                       required_options=['IA'],
                                                       required_err_msg=err_msg)
zhinst.utils.api_server_version_check(daq)
zhinst.utils.disable_everything(daq, device)

# We use the auto-range example before the next point


imp_index = 0
exp_settings = [['/%s/imps/%d/enable' % (device, imp_index), 1],
                    ['/%s/imps/%d/mode' % (device, imp_index), 0],
                    ['/%s/imps/%d/auto/output' % (device, imp_index), 1],
                    ['/%s/imps/%d/auto/bw' % (device, imp_index), 1],
                    ['/%s/imps/%d/bias/enable' % (device, imp_index), 1],
                    ['/%s/imps/%d/bias/value' % (device, imp_index), 0],
                    ['/%s/imps/%d/freq' % (device, imp_index), 1000],
                    ['/%s/imps/%d/auto/inputrange' % (device, imp_index), 1],
                    ['/%s/imps/%d/output/amplitude' % (device, imp_index), 0.1],
                    ['/%s/imps/%d/output/range'% (device, imp_index), 10],
                    ['/%s/imps/%d/model'% (device, imp_index), 0]]


# Subscribe to the impedance sample node path.
path = '/%s/imps/%d/sample' % (device, imp_index)
daq.set(exp_settings)
daq.sync()

amp_list = []
the_list = []
c_list=[]

'''for y in np.logspace(3, 6, 101): #freq
    daq.setDouble('/%s/imps/%d/freq' % (device, imp_index), y)
    for x in np.linspace(0.0, 2.0, 101): #bias/value, 2V is enough to turn on the LED
        daq.setDouble('/%s/imps/%d/bias/value' % (device, imp_index), x)'''  
# if sweep DC-offset, MFIA always auto-ranges, this is not good the instrument lifetime

for x in np.linspace(1.0, 1.7, 201): #bias/value, 2V is enough to turn on the LED
    daq.setDouble('/%s/imps/%d/bias/value' % (device, imp_index), x)
    for y in np.logspace(3, 6, 201): #freq
        daq.setDouble('/%s/imps/%d/freq' % (device, imp_index), y)


        daq.sync() #synchronize settings
            
        daq.subscribe(path)
        sleep_length = 1.0
        time.sleep(sleep_length) #this is to ensure the transient is not captured
        poll_length = 0.1  # [s]
        poll_timeout = 500  # [ms]
        poll_flags = 0
        poll_return_flat_dict = True
        data = daq.poll(poll_length, poll_timeout, poll_flags, poll_return_flat_dict) #in the 19.05 API, replace with flat=True
        daq.unsubscribe('*')

        impedanceSample = data[path]
        amp_ = np.abs(np.mean(impedanceSample['z']))
        the_ = np.angle(np.mean(impedanceSample['z']))*180/np.pi  #convert radian into deg, phase can also be extracted from data directly
        c_ = np.mean(impedanceSample['param1']) ##this presumes MFIA is using R||C model
        
        
        amp_list.append(amp_)
        the_list.append(the_)
        c_list.append(c_)

amp_array = np.array(amp_list).reshape(201,201) #convert into 2D matrix, and flip later x and y for easy plotting
the_array = np.array(the_list).reshape(201,201)
c_array = np.array(c_list).reshape(201,201)

real_array = amp_array*np.cos(the_array*np.pi/180) 
imag_array = amp_array*np.sin(the_array*np.pi/180)


'''This part can be used to show the original 2D amplitude and theta plots

plt.close('all')
X, Y = np.meshgrid(np.linspace(1.0, 1.7, 201), np.logspace(3, 6, 201))


fig0, ax0 = plt.subplots()
cs0 = ax0.contourf(X, Y, np.transpose(amp_array), locator=ticker.LogLocator(), cmap=cm.PuBu_r)
ax0.set_title('Impedance (Ohm)')
ax0.set_xlabel('DC bias (V)')
ax0.set_yscale('log')
ax0.set_ylabel('Frequency (Hz)')
ax0.autoscale()
cbar = fig0.colorbar(cs0)   
plt.draw()
plt.show()
    
fig1, ax1 = plt.subplots()
cs1 = ax1.contourf(X, Y, np.transpose(the_array), locator=ticker.LinearLocator(), cmap=cm.RuBu_r)
ax1.set_title('Phase (Deg)')
ax1.set_xlabel('DC bias (V)')
ax1.set_yscale('log')
ax1.set_ylabel('Frequency (Hz)')
ax1.autoscale()
cbar = fig1.colorbar(cs1)

'''

###here the data is excerpted only up to 1.56 V to avoid meaningless negative capacitance values at high DC bias

X, Y = np.meshgrid(np.linspace(1.0, 1.56, 160), np.logspace(3, 6, 201))


amp_array_sub=amp_array[0:160]
the_array_sub=the_array[0:160]
c_array_sub=c_array[0:160]

real_array_sub = real_array[::20]
imag_array_sub = imag_array[::20]


fig0, ax0 = plt.subplots()
cs0 = ax0.contourf(X, Y, np.transpose(amp_array_sub), locator=ticker.LogLocator(), cmap=cm.PuBu_r)
ax0.set_title('Impedance (Ohm)')
ax0.set_xlabel('DC bias (V)')
ax0.set_yscale('log')
ax0.set_ylabel('Frequency (Hz)')
ax0.autoscale()
cbar = fig0.colorbar(cs0)   
plt.draw()
plt.show()
    
fig1, ax1 = plt.subplots()
cs1 = ax1.contourf(X, Y, np.transpose(the_array_sub), locator=ticker.LinearLocator(), cmap=cm.PuBu_r)
ax1.set_title('Phase (Deg)')
ax1.set_xlabel('DC bias (V)')
ax1.set_yscale('log')
ax1.set_ylabel('Frequency (Hz)')
ax1.autoscale()
cbar = fig1.colorbar(cs1)   
plt.draw()
plt.show()

fig2, ax2 = plt.subplots()
cs2 = ax2.contourf(X, Y, np.transpose(c_array_sub), locator=ticker.LinearLocator(20), cmap=cm.PuBu_r)
ax2.set_title('Capacitance (F)')
ax2.set_xlabel('DC bias (V)')
ax2.set_yscale('log')
ax2.set_ylabel('Frequency (Hz)')
ax2.autoscale()
cbar = fig2.colorbar(cs2)   
plt.draw()
plt.show()

##Nyquist plot

fig3, ax3 = plt.subplots()
plt.plot(np.transpose(real_array_sub), -1*np.transpose(imag_array_sub)) #plot in 0.07V DC step
plt.ticklabel_format(style='sci', scilimits=(0,0))
ax3.set_title('    Nyquist plot at different DC bias at a step of 0.07 V')
ax3.set_xlabel('Real Z (Ohm)')
ax3.set_ylabel('-Imaginary Z (Ohm)')
plt.axis('equal')
ax3.autoscale()
ax3.set(xlim=(0, 6000000), ylim=(0,6000000)) #adjust to fit into the scale of the largest impedance range

plt.draw()
plt.show()
    
daq.setDouble('/%s/imps/%d/bias/value' % (device, imp_index), 0) # to turn off the LED
daq.setDouble('/%s/imps/%d/freq' % (device, imp_index), 1000)

pd.DataFrame(amp_array).to_csv('amp.csv') #save for post processing. These are enough to reconstruct other impedance parameters
pd.DataFrame(the_array).to_csv('the.csv')
pd.DataFrame(c_array).to_csv('c.csv')


# In[15]:


X, Y = np.meshgrid(np.linspace(1.0, 1.56, 160), np.logspace(3, 6, 201))


amp_array_sub=amp_array[0:160]
the_array_sub=the_array[0:160]
c_array_sub=c_array[0:160]

fig0, ax0 = plt.subplots()
cs0 = ax0.contourf(X, Y, np.transpose(amp_array_sub), locator=ticker.LogLocator(), cmap=cm.PuBu_r)
ax0.set_title('Impedance (Ohm)')
ax0.set_xlabel('DC bias (V)')
ax0.set_yscale('log')
ax0.set_ylabel('Frequency (Hz)')
ax0.autoscale()
cbar = fig0.colorbar(cs0)   
plt.draw()
plt.show()
    
fig1, ax1 = plt.subplots()
cs1 = ax1.contourf(X, Y, np.transpose(the_array_sub), locator=ticker.LinearLocator(), cmap=cm.PuBu_r)
ax1.set_title('Phase (Deg)')
ax1.set_xlabel('DC bias (V)')
ax1.set_yscale('log')
ax1.set_ylabel('Frequency (Hz)')
ax1.autoscale()
cbar = fig1.colorbar(cs1)   
plt.draw()
plt.show()

fig2, ax2 = plt.subplots()
cs2 = ax2.contourf(X, Y, np.transpose(c_array_sub), locator=ticker.LinearLocator(20), cmap=cm.PuBu_r)
ax2.set_title('Capacitance (F)')
ax2.set_xlabel('DC bias (V)')
ax2.set_yscale('log')
ax2.set_ylabel('Frequency (Hz)')
ax2.autoscale()
cbar = fig2.colorbar(cs2)   
plt.draw()
plt.show()

##Nyquist plot

fig3, ax3 = plt.subplots()
plt.plot(np.transpose(real_array[::20]), -1*np.transpose(imag_array[::20])) #plot in 0.07V DC step
plt.ticklabel_format(style='sci', scilimits=(0,0))
ax3.set_title('    Nyquist plot at different DC bias at a step of 0.07 V')
ax3.set_xlabel('Real Z (Ohm)')
ax3.set_ylabel('-Imaginary Z (Ohm)')
plt.axis('equal')
ax3.autoscale()
ax3.set(xlim=(0, 6000000), ylim=(0,6000000)) #adjust to fit into the scale of the largest impedance range

plt.draw()
plt.show()


# In[11]:


# -*- coding: utf-8 -*-
"""
Zurich Instruments LabOne Python API Example

Demonstrate how to perform a simple frequency sweep using the ziDAQSweeper
class/Sweeper Module.
"""

# Copyright 2016 Zurich Instruments AG

from __future__ import print_function
import time
import numpy as np
import zhinst.utils


def run_example(device_id, amplitude=0.1, do_plot=False):
    """
    Run the example: Perform a frequency sweep and record demodulator data using
    ziPython's ziDAQSweeper module.

    Requirements:

      Hardware configuration: Connect signal output 1 to signal input 1 with a
      BNC cable.

    Arguments:

      device_id (str): The ID of the device to run the example with. For
        example, `dev2006` or `uhf-dev2006`.

      amplitude (float, optional): The amplitude to set on the signal output.

      do_plot (bool, optional): Specify whether to plot the sweep. Default is no
        plot output.

    Returns:

      sample (list of dict): A list of demodulator sample dictionaries. Each
        entry in the list correspond to the result of a single sweep and is a
        dict containing a demodulator sample.

    Raises:

      RuntimeError: If the device is not "discoverable" from the API.

    See the "LabOne Programing Manual" for further help, available:
      - On Windows via the Start-Menu:
        Programs -> Zurich Instruments -> Documentation
      - On Linux in the LabOne .tar.gz archive in the "Documentation"
        sub-folder.

    """

    apilevel_example = 6  # The API level supported by this example.
    # Call a zhinst utility function that returns:
    # - an API session `daq` in order to communicate with devices via the data server.
    # - the device ID string that specifies the device branch in the server's node hierarchy.
    # - the device's discovery properties.
    err_msg = "This example only supports instruments with demodulators."
    (daq, device, props) = zhinst.utils.create_api_session(device_id, apilevel_example,
                                                           required_devtype='.*LI|.*IA|.*IS',
                                                           required_err_msg=err_msg)
    zhinst.utils.api_server_version_check(daq)

    # Create a base configuration: Disable all available outputs, awgs, demods, scopes,...
    zhinst.utils.disable_everything(daq, device)

    # Now configure the instrument for this experiment. The following channels
    # and indices work on all device configurations. The values below may be
    # changed if the instrument has multiple input/output channels and/or either
    # the Multifrequency or Multidemodulator options installed.
    out_channel = 0
    out_mixer_channel = zhinst.utils.default_output_mixer_channel(props)
    in_channel = 0
    demod_index = 0
    osc_index = 0
    demod_rate = 10e3
    time_constant = 0.01
    exp_setting = [['/%s/sigins/%d/ac'             % (device, in_channel), 0],
                   ['/%s/sigins/%d/range'          % (device, in_channel), 2*amplitude],
                   ['/%s/demods/%d/enable'         % (device, demod_index), 1],
                   ['/%s/demods/%d/rate'           % (device, demod_index), demod_rate],
                   ['/%s/demods/%d/adcselect'      % (device, demod_index), in_channel],
                   ['/%s/demods/%d/order'          % (device, demod_index), 4],
                   ['/%s/demods/%d/timeconstant'   % (device, demod_index), time_constant],
                   ['/%s/demods/%d/oscselect'      % (device, demod_index), osc_index],
                   ['/%s/demods/%d/harmonic'       % (device, demod_index), 1],
                   ['/%s/sigouts/%d/on'            % (device, out_channel), 1],
                   ['/%s/sigouts/%d/enables/%d'    % (device, out_channel, out_mixer_channel), 1],
                   ['/%s/sigouts/%d/range'         % (device, out_channel), 1],
                   ['/%s/sigouts/%d/amplitudes/%d' % (device, out_channel, out_mixer_channel), amplitude]]
    daq.set(exp_setting)

    # Perform a global synchronisation between the device and the data server:
    # Ensure that 1. the settings have taken effect on the device before issuing
    # the poll() command and 2. clear the API's data buffers.
    daq.sync()

    # Create an instance of the Sweeper Module (ziDAQSweeper class).
    sweeper = daq.sweep()

    # Configure the Sweeper Module's parameters.
    # Set the device that will be used for the sweep - this parameter must be set.
    sweeper.set('sweep/device', device)
    # Specify the `gridnode`: The instrument node that we will sweep, the device
    # setting corresponding to this node path will be changed by the sweeper.
    sweeper.set('sweep/gridnode', 'oscs/%d/freq' % osc_index)
    # Set the `start` and `stop` values of the gridnode value interval we will use in the sweep.
    sweeper.set('sweep/start', 0.01)
    if props['devicetype'].startswith('MF'):
        stop = 500e3
    else:
        stop = 50e6
    sweeper.set('sweep/stop', stop)
    # Set the number of points to use for the sweep, the number of gridnode
    # setting values will use in the interval (`start`, `stop`).
    samplecount = 100
    sweeper.set('sweep/samplecount', samplecount)
    # Specify logarithmic spacing for the values in the sweep interval.
    sweeper.set('sweep/xmapping', 2)
    # Automatically control the demodulator bandwidth/time constants used.
    # 0=manual, 1=fixed, 2=auto
    # Note: to use manual and fixed, sweep/bandwidth has to be set to a value > 0.
    sweeper.set('sweep/bandwidthcontrol', 1)
    # Sets the bandwidth overlap mode (default 0). If enabled, the bandwidth of
    # a sweep point may overlap with the frequency of neighboring sweep
    # points. The effective bandwidth is only limited by the maximal bandwidth
    # setting and omega suppression. As a result, the bandwidth is independent
    # of the number of sweep points. For frequency response analysis bandwidth
    # overlap should be enabled to achieve maximal sweep speed (default: 0). 0 =
    # Disable, 1 = Enable.
    sweeper.set('sweep/bandwidthoverlap', 0)

    # Sequential scanning mode (as opposed to binary or bidirectional).
    sweeper.set('sweep/scan', 0)
    # Specify the number of sweeps to perform back-to-back.
    loopcount = 1
    sweeper.set('sweep/loopcount', loopcount)
    # We don't require a fixed sweep/settling/time since there is no DUT
    # involved in this example's setup (only a simple feedback cable), so we set
    # this to zero. We need only wait for the filter response to settle,
    # specified via sweep/settling/inaccuracy.
    sweeper.set('sweep/settling/time', 0)
    # The sweep/settling/inaccuracy' parameter defines the settling time the
    # sweeper should wait before changing a sweep parameter and recording the next
    # sweep data point. The settling time is calculated from the specified
    # proportion of a step response function that should remain. The value
    # provided here, 0.001, is appropriate for fast and reasonably accurate
    # amplitude measurements. For precise noise measurements it should be set to
    # ~100n.
    # Note: The actual time the sweeper waits before recording data is the maximum
    # time specified by sweep/settling/time and defined by
    # sweep/settling/inaccuracy.
    sweeper.set('sweep/settling/inaccuracy', 0.001)
    # Set the minimum time to record and average data to 10 demodulator
    # filter time constants.
    sweeper.set('sweep/averaging/tc', 10)
    # Minimal number of samples that we want to record and average is 100. Note,
    # the number of samples used for averaging will be the maximum number of
    # samples specified by either sweep/averaging/tc or sweep/averaging/sample.
    sweeper.set('sweep/averaging/sample', 10)

    # Now subscribe to the nodes from which data will be recorded. Note, this is
    # not the subscribe from ziDAQServer; it is a Module subscribe. The Sweeper
    # Module needs to subscribe to the nodes it will return data for.x
    path = '/%s/demods/%d/sample' % (device, demod_index)
    sweeper.subscribe(path)

    # Start the Sweeper's thread.
    sweeper.execute()

    start = time.time()
    timeout = 1000  # [s]
    print("Will perform", loopcount, "sweeps...")
    while not sweeper.finished():  # Wait until the sweep is complete, with timeout.
        time.sleep(0.2)
        progress = sweeper.progress()
        print("Individual sweep progress: {:.2%}.".format(progress[0]), end="\r")
        # Here we could read intermediate data via:
        # data = sweeper.read(True)...
        # and process it while the sweep is completing.
        # if device in data:
        # ...
        if (time.time() - start) > timeout:
            # If for some reason the sweep is blocking, force the end of the
            # measurement.
            print("\nSweep still not finished, forcing finish...")
            sweeper.finish()
    print("")

    # Read the sweep data. This command can also be executed whilst sweeping
    # (before finished() is True), in this case sweep data up to that time point
    # is returned. It's still necessary still need to issue read() at the end to
    # fetch the rest.
    return_flat_dict = True
    
    #sweeper.saveonread('abcsw')
    data = sweeper.read(return_flat_dict)
    #print (data)
    sweeper.unsubscribe(path)

    # Stop the sweeper thread and clear the memory.
    sweeper.clear()

    # Check the dictionary returned is non-empty.
    assert data, "read() returned an empty data dictionary, did you subscribe to any paths?"
    # Note: data could be empty if no data arrived, e.g., if the demods were
    # disabled or had rate 0.
    assert path in data, "No sweep data in data dictionary: it has no key '%s'" % path
    samples = data[path]
    print("Returned sweeper data contains", len(samples), "sweeps.")
    assert len(samples) == loopcount,         "The sweeper returned an unexpected number of sweeps: `%d`. Expected: `%d`." % (len(samples), loopcount)

    if do_plot:
        import matplotlib.pyplot as plt
        _, (ax1, ax2) = plt.subplots(2, 1)

        for sample in samples:
            frequency = sample[0]['frequency']
            R = np.abs(sample[0]['x'] + 1j*sample[0]['y'])
            phi = np.angle(sample[0]['x'] + 1j*sample[0]['y'])
            ax1.plot(frequency, R)
            ax2.plot(frequency, phi)
        ax1.set_title('Results of %d sweeps.' % len(samples))
        ax1.grid()
        ax1.set_ylabel(r'Demodulator R ($V_\mathrm{RMS}$)')
        ax1.set_xscale('log')
        ax1.set_ylim(0.0, 0.1)

        ax2.grid()
        ax2.set_xlabel('Frequency ($Hz$)')
        ax2.set_ylabel(r'Demodulator Phi (radians)')
        ax2.set_xscale('log')
        ax2.autoscale()

        plt.draw()
        plt.show()

    return samples


# In[14]:


run_example('dev4220', amplitude=0.1, do_plot=True)


# In[4]:


abc


# In[1]:


amplitude = 0.1
apilevel_example = 6  # The API level supported by this example.
# Call a zhinst utility function that returns:
# - an API session `daq` in order to communicate with devices via the data server.
# - the device ID string that specifies the device branch in the server's node hierarchy.
# - the device's discovery properties.
err_msg = "This example only supports instruments with demodulators."
(daq, device, props) = zhinst.utils.create_api_session('dev4220', apilevel_example,
                                                       required_devtype='.*LI|.*IA|.*IS',
                                                       required_err_msg=err_msg)
zhinst.utils.api_server_version_check(daq)

# Create a base configuration: Disable all available outputs, awgs, demods, scopes,...
zhinst.utils.disable_everything(daq, device)

# Now configure the instrument for this experiment. The following channels
# and indices work on all device configurations. The values below may be
# changed if the instrument has multiple input/output channels and/or either
# the Multifrequency or Multidemodulator options installed.
out_channel = 0
out_mixer_channel = zhinst.utils.default_output_mixer_channel(props)
in_channel = 0
demod_index = 0
osc_index = 0
demod_rate = 10e3
time_constant = 0.01
h = daq.sweep()

h.set('sweep/save/directory', 'C:\\Users\\mengl\\Documents\\Zurich Instruments\\LabOne\\WebServer')
exp_setting = [['/%s/sigins/%d/ac'             % (device, in_channel), 0],
               ['/%s/sigins/%d/range'          % (device, in_channel), 2*amplitude],
               ['/%s/demods/%d/enable'         % (device, demod_index), 1],
               ['/%s/demods/%d/rate'           % (device, demod_index), demod_rate],
               ['/%s/demods/%d/adcselect'      % (device, demod_index), in_channel],
               ['/%s/demods/%d/order'          % (device, demod_index), 4],
               ['/%s/demods/%d/timeconstant'   % (device, demod_index), time_constant],
               ['/%s/demods/%d/oscselect'      % (device, demod_index), osc_index],
               ['/%s/demods/%d/harmonic'       % (device, demod_index), 1],
               ['/%s/sigouts/%d/on'            % (device, out_channel), 1],
               ['/%s/sigouts/%d/enables/%d'    % (device, out_channel, out_mixer_channel), 1],
               ['/%s/sigouts/%d/range'         % (device, out_channel), 1],
               ['/%s/sigouts/%d/amplitudes/%d' % (device, out_channel, out_mixer_channel), amplitude]]
daq.set(exp_setting)

# Perform a global synchronisation between the device and the data server:
# Ensure that 1. the settings have taken effect on the device before issuing
# the poll() command and 2. clear the API's data buffers.
daq.sync()

# Create an instance of the Sweeper Module (ziDAQSweeper class).
sweeper = daq.sweep()

# Configure the Sweeper Module's parameters.
# Set the device that will be used for the sweep - this parameter must be set.
sweeper.set('sweep/device', device)
# Specify the `gridnode`: The instrument node that we will sweep, the device
# setting corresponding to this node path will be changed by the sweeper.
sweeper.set('sweep/gridnode', 'oscs/%d/freq' % osc_index)
# Set the `start` and `stop` values of the gridnode value interval we will use in the sweep.
sweeper.set('sweep/start', 0.01)
if props['devicetype'].startswith('MF'):
    stop = 500e3
else:
    stop = 50e6
sweeper.set('sweep/stop', stop)
# Set the number of points to use for the sweep, the number of gridnode
# setting values will use in the interval (`start`, `stop`).
samplecount = 100
sweeper.set('sweep/samplecount', samplecount)
# Specify logarithmic spacing for the values in the sweep interval.
sweeper.set('sweep/xmapping', 2)
# Automatically control the demodulator bandwidth/time constants used.
# 0=manual, 1=fixed, 2=auto
# Note: to use manual and fixed, sweep/bandwidth has to be set to a value > 0.
sweeper.set('sweep/bandwidthcontrol', 1)
# Sets the bandwidth overlap mode (default 0). If enabled, the bandwidth of
# a sweep point may overlap with the frequency of neighboring sweep
# points. The effective bandwidth is only limited by the maximal bandwidth
# setting and omega suppression. As a result, the bandwidth is independent
# of the number of sweep points. For frequency response analysis bandwidth
# overlap should be enabled to achieve maximal sweep speed (default: 0). 0 =
# Disable, 1 = Enable.
sweeper.set('sweep/bandwidthoverlap', 0)

# Sequential scanning mode (as opposed to binary or bidirectional).
sweeper.set('sweep/scan', 0)
# Specify the number of sweeps to perform back-to-back.
loopcount = 1
sweeper.set('sweep/loopcount', loopcount)
# We don't require a fixed sweep/settling/time since there is no DUT
# involved in this example's setup (only a simple feedback cable), so we set
# this to zero. We need only wait for the filter response to settle,
# specified via sweep/settling/inaccuracy.
sweeper.set('sweep/settling/time', 0)
# The sweep/settling/inaccuracy' parameter defines the settling time the
# sweeper should wait before changing a sweep parameter and recording the next
# sweep data point. The settling time is calculated from the specified
# proportion of a step response function that should remain. The value
# provided here, 0.001, is appropriate for fast and reasonably accurate
# amplitude measurements. For precise noise measurements it should be set to
# ~100n.
# Note: The actual time the sweeper waits before recording data is the maximum
# time specified by sweep/settling/time and defined by
# sweep/settling/inaccuracy.
sweeper.set('sweep/settling/inaccuracy', 0.001)
# Set the minimum time to record and average data to 10 demodulator
# filter time constants.
sweeper.set('sweep/averaging/tc', 10)
# Minimal number of samples that we want to record and average is 100. Note,
# the number of samples used for averaging will be the maximum number of
# samples specified by either sweep/averaging/tc or sweep/averaging/sample.
sweeper.set('sweep/averaging/sample', 10)

# Now subscribe to the nodes from which data will be recorded. Note, this is
# not the subscribe from ziDAQServer; it is a Module subscribe. The Sweeper
# Module needs to subscribe to the nodes it will return data for.x
path = '/%s/demods/%d/sample' % (device, demod_index)
sweeper.subscribe(path)

# Start the Sweeper's thread.
sweeper.execute()

start = time.time()
timeout = 1000  # [s]
print("Will perform", loopcount, "sweeps...")
while not sweeper.finished():  # Wait until the sweep is complete, with timeout.
    time.sleep(0.2)
    progress = sweeper.progress()
    print("Individual sweep progress: {:.2%}.".format(progress[0]), end="\r")
    # Here we could read intermediate data via:
    # data = sweeper.read(True)...
    # and process it while the sweep is completing.
    # if device in data:
    # ...
    if (time.time() - start) > timeout:
        # If for some reason the sweep is blocking, force the end of the
        # measurement.
        print("\nSweep still not finished, forcing finish...")
        sweeper.finish()
print("")

# Read the sweep data. This command can also be executed whilst sweeping
# (before finished() is True), in this case sweep data up to that time point
# is returned. It's still necessary still need to issue read() at the end to
# fetch the rest.
return_flat_dict = True
data = sweeper.read(return_flat_dict)

sweeper.unsubscribe(path)
sweeper.save('abcdefg')
# Stop the sweeper thread and clear the memory.
sweeper.clear()

# Check the dictionary returned is non-empty.
assert data, "read() returned an empty data dictionary, did you subscribe to any paths?"
# Note: data could be empty if no data arrived, e.g., if the demods were
# disabled or had rate 0.
assert path in data, "No sweep data in data dictionary: it has no key '%s'" % path
samples = data[path]
print("Returned sweeper data contains", len(samples), "sweeps.")
assert len(samples) == loopcount,     "The sweeper returned an unexpected number of sweeps: `%d`. Expected: `%d`." % (len(samples), loopcount)


# In[30]:


sweeper = daq.sweep()
sweeper.save('ab')


# In[31]:


ab


# In[32]:


sweeper.load('ab')


# In[8]:


import zhinst.ziPython as ziPython
help(ziPython.SweeperModule)


# In[35]:


ziPython.SweeperModule


# In[ ]:




