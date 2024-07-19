# Copyright 2024 Zurich Instruments AG
# Application: This script implements Q-Control method for a resonator using lock-in amplifiers. 
# Instruments: MFLI, UHFLI
# Options: PID, MF (MD for MFLI)
# Setup: 1.84-MHz resonator between Signal Input 1 and Signal Output 1 


from zhinst.core import ziDAQServer
import time


def api_session(device, host, interface):
    # API connection to the instrument
    session = ziDAQServer(host, 8004, 6)
    session.connectDevice(device, interface)
    return session


def device_initialization(session, device):
    # Initial settings for Q control
    session.syncSetInt(f'/{device}/system/preset/index', 0)
    session.syncSetInt(f'/{device}/system/preset/load', 0)
    time.sleep(3)
    initial_settings = [
        # Signal Output
        (f'/{device}/sigouts/0/on', 0),
        (f'/{device}/sigouts/0/imp50', 0),
        (f'/{device}/sigouts/0/add', 0),
        (f'/{device}/sigouts/0/range', 1.0),
        (f'/{device}/sigouts/0/offset', 0.0),
        (f'/{device}/sigouts/0/diff', 0),
        (f'/{device}/sigouts/0/amplitudes/0', 0.00),
        (f'/{device}/sigouts/0/amplitudes/1', 0.0),
        (f'/{device}/sigouts/0/amplitudes/2', 0.0),
        (f'/{device}/sigouts/0/amplitudes/3', 0.0),
        (f'/{device}/sigouts/0/enables/0', 0),
        (f'/{device}/sigouts/0/enables/1', 1),
        (f'/{device}/sigouts/0/enables/2', 1),
        (f'/{device}/sigouts/0/enables/3', 1),
        # Signal Input
        (f'/{device}/sigins/0/imp50', 1),
        (f'/{device}/sigins/0/float', 0),
        (f'/{device}/sigins/0/diff', 0),
        (f'/{device}/sigins/0/ac', 0),
        (f'/{device}/sigins/0/range', 0.3),
        # Demodulators
        (f'/{device}/extrefs/*/enable', 0),
        (f'/{device}/demods/*/oscselect', 0),
        (f'/{device}/demods/*/harmonic', 1),
        (f'/{device}/demods/0/phaseshift', 0.0),
        (f'/{device}/demods/1/phaseshift', 0.0),
        (f'/{device}/demods/2/phaseshift', 0.0),
        (f'/{device}/demods/3/phaseshift', 90.0),
        (f'/{device}/demods/*/adcselect', 0),
        # PIDs
        (f'/{device}/pids/*/enable', 0),
        (f'/{device}/pids/2/input', 0),
        (f'/{device}/pids/3/input', 1),
        (f'/{device}/pids/2/inputchannel', 0),
        (f'/{device}/pids/3/inputchannel', 0),
        (f'/{device}/pids/2/setpoint', 0.0),
        (f'/{device}/pids/3/setpoint', 0.0),
        (f'/{device}/pids/2/demod/timeconstant', 0.5e-3),
        (f'/{device}/pids/3/demod/timeconstant', 0.5e-3),
        (f'/{device}/pids/2/demod/order', 4),
        (f'/{device}/pids/3/demod/order', 4),
        (f'/{device}/pids/2/demod/harmonic', 1),
        (f'/{device}/pids/3/demod/harmonic', 1),
        (f'/{device}/pids/2/output', 0),
        (f'/{device}/pids/3/output', 0),
        (f'/{device}/pids/2/outputchannel', 2),
        (f'/{device}/pids/3/outputchannel', 3),
        (f'/{device}/pids/2/center', 0.0),
        (f'/{device}/pids/3/center', 0.0),
        (f'/{device}/pids/2/limitlower', -0.5),
        (f'/{device}/pids/3/limitlower', -0.5),
        (f'/{device}/pids/2/limitupper', +0.5),
        (f'/{device}/pids/3/limitupper', +0.5),
        (f'/{device}/pids/2/p', 0.0),
        (f'/{device}/pids/3/p', 0.0),
        (f'/{device}/pids/2/i', 0.0),
        (f'/{device}/pids/3/i', 0.0),
        (f'/{device}/pids/2/d', 0.0),
        (f'/{device}/pids/3/d', 0.0),
        (f'/{device}/pids/2/keepint', 0),
        (f'/{device}/pids/3/keepint', 0),
    ]
    session.set(initial_settings)


def drive_signal_output(session, device, amplitude):
    drive_settings = [
        (f'/{device}/sigouts/0/amplitudes/1', amplitude),
        (f'/{device}/pids/2/enable', 1),
        (f'/{device}/pids/3/enable', 1),
        (f'/{device}/sigouts/0/on', 1),
    ]
    session.set(drive_settings)


def adjust_feedback_gain(session, device, gain):
    feedback_settings = [
        (f'/{device}/pids/2/p', - gain),
        (f'/{device}/pids/3/p', - gain),
    ]
    session.set(feedback_settings)


if __name__ == "__main__":
    
    device = "dev4022"
    host = "10.42.5.62"
    interface = "PCIe"
    #device = "dev2730"
    #host = "127.0.0.1"
    #interface = "1GbE"
    
    daq = api_session(device, host, interface)
    device_initialization(daq, device)
    
    resonance_frequency = 1.84342276e6    # [Hz]
    daq.set(f'/{device}/oscs/0/freq', resonance_frequency),

    driving_amplitude = 0.1    # [V]
    drive_signal_output(daq, device, driving_amplitude)

    feedback_gain = +10    # []
    adjust_feedback_gain(daq, device, feedback_gain)
