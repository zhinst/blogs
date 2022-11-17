---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.14.1
  kernelspec:
    display_name: Python 3.10.0
    language: python
    name: python3
---

# Waveform Precision in Picoseconds: Subsampling Techniques with Zurich Instruments QCCS

This script implements an example sequence that sets the wait time between two pulses to sub-sample precision, as described in the blog post.

Copyright (C) 2022 Zurich Instruments

This software may be modified and distributed under the terms of the MIT license. See the LICENSE file for details.


## Imports

```python
# Import what we need to get started:
from laboneq.simple import DeviceSetup, Session
from zhinst.toolkit import CommandTable, Sequence

from itertools import count
```

## Descriptor and Device Setup


Labone Q uses a descriptor file containing the list of intstruments to be used in an experiment. Edit the descriptor YAML to include your device's ID and include your IP address or `localhost` below when running this notebook on your own setup. You can read about the details of defining a descriptor here: https://docs.zhinst.com/labone_q_user_manual/concepts/set_up_equipment.html

```python
setup_descriptor = '''
instrument_list:
  #HDAWG:
  #- address: 'DEVXXXX'
  #  uid: device
  SHFQC:
  - address: 'DEVXXXXX'
    uid: device
connections:
  #device:
  #  - rf_signal: none/none
  #    ports: [SIGOUTS/0]
  device:
    - iq_signal: none/none
      ports: [SGCHANNELS/0/OUTPUT]
'''

# Define the DeviceSetup from descriptor - 
# Additionally include information on the dataserver used to connect to the instruments 
my_setup = DeviceSetup.from_descriptor(
    setup_descriptor,
    server_host='localhost',
    server_port='8004',
    setup_name='Setup_Name',
) 

# The target AWG in the instrument
AWG_CORE_INDEX = 0
```

## Session


We etablish a connection to the device with the `Session` class.

```python
# Connect to the Session
my_session = Session(device_setup=my_setup)
my_session.connect(do_emulation=False) # Note: Emulation is not supported when using the Toolkit!
```

### Accessing Device Nodes


We make the following assignments and definitions to access the nodes using the Toolkit from within LabOne Q. In a LabOne Q Session, each device that has been connected to can be accessed using its device ID.

```python
instrument_serial = my_setup.instrument_by_uid('device').address
device = my_session.devices[instrument_serial]
```

```python
#Detect the device type
if device.device_type.startswith('SHFSG') or device.device_type.startswith('SHFQC'):
    device_type = 'sg'
elif device.device_type.startswith('HDAWG'):
    device_type = 'hd'
else:
    raise RuntimeError('Unsupported device for this experiment')

#Fetch the AWG and channel nodes
if device_type == 'sg':
    awg = sgchannel.awg
    sgchannel = device.sgchannels[AWG_CORE_INDEX]
elif device_type == 'hd':
    awg = device.awgs[AWG_CORE_INDEX]
    out_ch = [2*AWG_CORE_INDEX, 2*AWG_CORE_INDEX+1]
```

### Reset to a Default State


If you'd like to reset your device, turn off all ouputs, and revert to the default state, you can uncomment the reset command below. Note that while the HDAWG supports this functionality, some other Zurich Instruments products do not.

```python
# Reset the device to its factory settings before beginning tutorial
#device.factory_reset()
```

## Apply Instrument Settings


We use a transactional set to simultaneously push all of our desired settings to the HDAWG:

```python
# use transactional set to configure multiple settings
with device.set_transaction():
    awg.single(True)                                              # Disable 'Rerun' of AWG sequencer
    if device_type == 'sg':
        awg.modulation.enable(False)                              # No modulation
        awg.outputamplitude(0.5)                                  # Amplitude to 0.5 to not saturate the output
        awg.outputs[0].gains[0](1.0)                              # Set the correct output gain
        awg.outputs[0].gains[1](-1.0)
        awg.outputs[1].gains[0](1.0)
        awg.outputs[1].gains[1](1.0)

        sgchannel.marker.source('output0_marker0')                # Set the marker output

        sgchannel.digitalmixer.centerfreq(0.0)                    # No modulation
        sgchannel.output.rflfpath('lf')                           # Use LF path
        sgchannel.output.range(0.0)                               # 0 dBm range
        sgchannel.output.on(True)                                 # Switch ON the output

    elif device_type == 'hd':
        device.system.awg.channelgrouping(0)                      # work in non-grouped mode (individual AWG cores)

        awg.outputs['*'].modulation.mode('off')                   # Disable digital modulation
        awg.outputs[0].gains[0](0.5)                              # Sets the Waveform Generator output amplitude
        awg.outputs[0].gains[1](0.0)
        awg.outputs[1].gains[0](0.0)
        awg.outputs[1].gains[1](0.5)

        device.triggers.out[out_ch[0]].source('output0_marker0')  # Set the marker output

        device.sigouts[out_ch].range(1.0)                         # Set output voltage range
        device.sigouts[out_ch].on(True)                           # Switch on the outputs
```

## Pulse Sequence


We now define our pulse, subsampling, and sample parameters. In the previous blog post, we shifted waveforms by one sample. Here, we retain the ability to utilize that single sample precision, and we add the functionality to control the spacing of our waveform by less than a sample!

```python
# Sequencer program for the AWG
seq = Sequence()
seq.constants['LEN_SECTION'] = 1024

# Waveform paramaters
seq.constants['PULSE_WIDTH'] = 1e-9 #ns
seq.constants['SIGMAS_PULSE'] = 6

# Sequence parameters
seq.constants['SUBSAMPLING_BITS'] = 2  # Bits to use for subsampling
seq.constants['T_START'] = 0           # Start wait time, in subsamples units (one step is 1/((2**SUBSAMPLING_BITS)*SAMPLE_RATE) second)
seq.constants['T_END'] = 320           # Stop wait time
seq.constants['T_STEP'] = 1            # Step wait time
seq.constants['SAMPLE_STEPS'] = 16     # Sample precise steps, given by the AWG granularity

#Readout parameters
seq.constants['TRIGGER_LEN'] = 32
seq.constants['READOUT_LEN'] = 1024

#Waveforms index
NUM_SHIFTED_ENTRIES = seq.constants['SAMPLE_STEPS'] * 2**seq.constants['SUBSAMPLING_BITS']
wfm_index = count(NUM_SHIFTED_ENTRIES)
seq.constants['WAVE_FIRST_INDEX'] = next(wfm_index)
seq.constants['TRG_INDEX'] = next(wfm_index)

#Command table parameters
ct_index = count(NUM_SHIFTED_ENTRIES)
seq.constants['TE_FIRST_PULSE'] = next(ct_index)
seq.constants['TE_READOUT_TRG'] = next(ct_index)

# Creation of the command table
ct = CommandTable(awg.commandtable.load_validation_schema())
# - Define all the shifted pulses
for i in range(NUM_SHIFTED_ENTRIES):
    ct.table[i].waveform.index = i

# - Plays the first pulse edge
te_first_pulse = ct.table[seq.constants['TE_FIRST_PULSE']]
te_first_pulse.waveform.index = seq.constants['WAVE_FIRST_INDEX']

# - Triggers the readout
te_readout_trg = ct.table[seq.constants['TE_READOUT_TRG']]
te_readout_trg.waveform.index = seq.constants['TRG_INDEX']

# Definition of the sequence to be uploaded to the device
seq.code = '''\
//Calculations
const PULSE_WIDTH_SAMPLE = PULSE_WIDTH*DEVICE_SAMPLE_RATE;                  //Can also define by samples (e.g. 1)
const PULSE_TOTAL_LEN = ceil(PULSE_WIDTH_SAMPLE*SIGMAS_PULSE*2/16)*16;      //Can also define by samples (e.g. 64)

const SUBSAMPLING = pow(2,SUBSAMPLING_BITS);                                //Number of subsampling steps
const ALL_BITS = SUBSAMPLING_BITS + 4;                                      //Number of bits used to encode the fine part of wait time (sample and subsample precise)

const MASK_FINE = pow(2,ALL_BITS) - 1;                                      //Mask to extract the fine part of wait time
const MASK_COARSE = -pow(2,ALL_BITS);                                       //Mask to extract the coarse part of wait time

//Waveform definition
wave pulse0 = gauss(PULSE_TOTAL_LEN, PULSE_TOTAL_LEN/2, PULSE_WIDTH_SAMPLE);
wave trigger = marker(TRIGGER_LEN, 1);

//Create shifted waveforms
cvar j,k;
for (j = 0; j < SAMPLE_STEPS; j++) {
  for (k = 0; k < SUBSAMPLING; k++) {
    cvar PULSE_CENTER = PULSE_TOTAL_LEN/2 + k/SUBSAMPLING;                  //Calculate the subsample shifted center
    wave pulse = gauss(PULSE_TOTAL_LEN, PULSE_CENTER, PULSE_WIDTH_SAMPLE);  //Create the k-subsamples shifted waveform
    wave w_shifted = join(zeros(j), pulse, zeros(16 - j));                  //Create the j-samples shifted waveform
    assignWaveIndex(1,2, w_shifted, SUBSAMPLING*j + k);                       //Assign index j to the waveform
  }
}

//Assign index and outputs
assignWaveIndex(1,2, pulse0, WAVE_FIRST_INDEX);
assignWaveIndex(trigger, TRG_INDEX);

while (true) {
  //Execution, no averaging
  var t = T_START;
  var t_fine, coarse, t_coarse;
  do {
      t_fine = t & MASK_FINE;                                               //The fine shift is the ALL_BITS least significant bits
      coarse = t & MASK_COARSE;                                             //Check if coarse delay is needed (boolean). Equivalent to (t >= ALL_BITS)
      t_coarse = t >> SUBSAMPLING_BITS;                                     //Extract the coarse wait time

      executeTableEntry(TE_FIRST_PULSE);                                    //Play first pulse, no shift
      if(coarse)
        playZero(t_coarse);                                                 //Evolution time t (coarse)
      executeTableEntry(t_fine);                                            //Play second pulse, fine shift

      executeTableEntry(TE_READOUT_TRG);                                    //Readout trigger
      playZero(READOUT_LEN);                                                //Readout time

      t += T_STEP;                                                          //Increase wait time
  } while (t < T_END);                                                      //Loop until the end
}
'''

#Load sequence and command table in the device
with device.set_transaction():
  awg.load_sequencer_program(seq)
  awg.commandtable.upload_to_device(ct)
```

## Run the Experiment


We enable the AWG and run our sequence.

```python
awg.enable(True)
```
