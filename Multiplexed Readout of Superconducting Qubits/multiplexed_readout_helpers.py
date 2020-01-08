# Copyright (C) 2020 Zurich Instruments
#
# This software may be modified and distributed under the terms
# of the MIT license. See the LICENSE file for details.

import numpy as np
import matplotlib.pyplot as plt
import textwrap
import time


def write_crosstalk_matrix(daq, device, matrix):
    """
    Writes the given matrix to the QA Setup crosstalk matrix of the UHFQA.

    Arguments:
        daq (zhinst.ziDAQServer) -- Connection to the Data Server
        device (String) -- device ID, e.g. "dev2266"
        matrix (2D array) -- crosstalk matrix to be written to the QA Setup tab
    """
    rows, cols = matrix.shape
    for r in range(rows):
        for c in range(cols):
            node = f"/{device}/qas/0/crosstalk/rows/{r}/cols/{c}"
            daq.setDouble(node, matrix[r, c])
    return


def sequence_multiplexed_readout(
    channels,
    frequencies,
    n_averages,
    state=None,
):
    """
    Returns an AWG sequence program (String) that specifies 
    the sequence for multiplexed readout. Amplitudes and phases 
    are hardcoded in the function for up to 10 channels and for 
    ground and excited qubit states (simulated response of a 
    readout resonator for qubit in either ground or excited state).

    Arguments:
        channels (int) -- indices of channels to create readout pulses for
        frequencies (float) -- frequencies (in Hz) of readout pulses
        n_averages )int) -- number of repetitions

    Keyword Arguments:
        state (int) -- states of measured channels to be simulated, 0 or 1

    Returns:
        (String) -- awg sequence program as string
    """

    # hard coded parameters for pulse parameters here... for ground and excited state (+ delta)
    amplitudes = np.array([0.13, 0.15, 0.16, 0.15, 0.14, 0.13, 0.17, 0.23, 0.19, 0.11])/20
    phases = np.zeros(10)
    deltas_amplitude = np.array([0.02, 0.01, -0.01, 0.02, -0.012, 0.0, 0.02, -0.012, 0.06, 0.03]) 
    deltas_phase = np.array([0.23, 0.31, 0.26, -0.171, 0.28, -0.31, 0.19, -0.21, 0.091, 0.29]) * np.pi /4
    
    n_channels = len(channels)
    assert len(frequencies) >= max(channels), "Not enough readout frequencies specified!"

    if state is None:
        state = [0] * n_channels
    
    for i, ch  in enumerate(channels):
        if frequencies[ch] < 0:
            frequencies[ch] = abs(frequencies[ch])
            # decide what to do here
        if state[i]:
            amplitudes[ch] = amplitudes[ch] * (1 + deltas_amplitude[ch])
            phases[ch] += deltas_phase[ch]
    
    # text snippet for the initialization of awg sequence
    awg_program_init = textwrap.dedent(
        """\
        const samplingRate = 1.8e9;
        // parameters for envelope
        const riseTime = 30e-9;
        const fallTime = 30e-9;
        const flatTime = 200e-9;
        const rise = riseTime * samplingRate;
        const fall = fallTime * samplingRate;
        const length = flatTime * samplingRate;
        const totalLength =  rise + length + fall;
        // define waveforms
        wave w_gauss_rise = gauss(2*rise, rise, rise/4);
        wave w_gauss_fall = gauss(2*fall, fall, fall/4);
        wave w_rise = cut(w_gauss_rise, 0, rise);
        wave w_fall = cut(w_gauss_fall, fall, 2*fall-1);
        wave w_flat = rect(length, 1.0); 
        wave w_pad = zeros((totalLength-1)%16);
        // combine to total envelope
        wave readoutPulse = 1.0*join(w_rise, w_flat, w_fall, w_pad) + 0.0* w_gauss_rise;

        // init empty final waveforms
        wave w_I = zeros(totalLength);
        wave w_Q = zeros(totalLength);

    """
    )

    # text snippet for single pulse
    awg_program_singlePulse = textwrap.dedent(
        """\
        // modulate envelope for readout pulse *N*
        const f*N*_readout = _Frequency*N*_ ;
        wave w*N*_I =  _Amplitude*N*_ * readoutPulse * cosine(totalLength, 1, _Phase*N*_, f*N*_readout*totalLength/samplingRate);
        wave w*N*_Q = _Amplitude*N*_ * readoutPulse * sine(totalLength, 1, _Phase*N*_, f*N*_readout*totalLength/samplingRate);
        w_I = add(w_I, w*N*_I);
        w_Q = add(w_Q, w*N*_Q);

    """
    )

    # text snippet for main loop of .seqC
    awg_program_playWave = textwrap.dedent(
        """\
        // play waveform
        setTrigger(AWG_INTEGRATION_ARM);
        var result_averages = _nAverages_ ;
        repeat (result_averages) {
            playWave(w_I, w_Q);
            setTrigger(AWG_INTEGRATION_ARM + AWG_INTEGRATION_TRIGGER + AWG_MONITOR_TRIGGER + 1);
            setTrigger(AWG_INTEGRATION_ARM);
            waitWave();
            wait(1024);
        }
        setTrigger(0);

    """
    )

    # add all the pulses for N = ... readout channels
    # add each channel and replace indices for readout frequencies ...
    awg_program_pulses = ""
    for ch in channels:
        awg_program_pulses = awg_program_pulses + awg_program_singlePulse.replace(
            "*N*", str(ch)
        )

    # replace parameters in sequence program
    awg_program_pulses = awg_program_pulses.replace("_nChannels_", str(n_channels))
    for ch in channels:
        awg_program_pulses = awg_program_pulses.replace(
            f"_Frequency{ch}_", str(frequencies[ch])
        )
        awg_program_pulses = awg_program_pulses.replace(
            f"_Amplitude{ch}_", str(amplitudes[ch])
        )
        awg_program_pulses = awg_program_pulses.replace(
            f"_Phase{ch}_", str(phases[ch])
        )
    awg_program_playWave = awg_program_playWave.replace("_nAverages_", str(n_averages))

    return awg_program_init + awg_program_pulses + awg_program_playWave


def compile_sequence(awg_module, awg_program):
    """
    Starts compilation of AWG sequence program dn loads it to device.

    Arguments:
        awg_module (awgModule) -- awgModule Object of AWG
        awg_program (String) -- specifies the awg sequence in .seqC format
    """
    awg_module.set("compiler/sourcestring", awg_program)
    while awg_module.getInt("compiler/status") == -1:
        time.sleep(0.1)
    assert awg_module.getInt("compiler/status") != 1, awg_module.getString(
        "/compiler/statusstring"
    )
    if awg_module.get("compiler/status") == 0:
        print("Compilation successful!")


def generate_demod_weights(length, frequency, samplingRate=1.8e9, plot=False, phase=0):
    assert length <= 4096
    assert frequency > 0
    x = np.arange(0, length)
    y = np.sin(2 * np.pi * frequency * x / samplingRate + phase)
    return y


def run_awg(daq, device):
    """
    Runs AWG sequence. Sets AWG to single shots and enables AWG.

    Arguments:
        daq (zhinst.ziDAQServer) -- Data Server Object
        device (String) -- device ID, e.g. "dev2266"
    """
    daq.asyncSetInt(f"/{device}/awgs/0/single", 1)
    daq.syncSetInt(f"/{device}/awgs/0/enable", 1)


def toggle_outputs(daq, device, channel=None):
    """
    Toggles signal output of UHFQA. If no channel specified toggles both.

    Arguments:
        daq (zhinst.ziDAQServer) -- Data Server Object
        device (String) -- device ID, e.g. "dev2266"

    Keyword Arguments:
        channel (int) -- list of channels to be toggled (in 0, 1) 
                            (default: None)
    """

    if channel is not None:
        assert channel in [0, 1]
        channel = [channel]
    else:
        channel = [0, 1]
    for ch in channel:
        path = f"/{device}/sigouts/{ch}/on"
        if daq.getInt(path) == 0:
            daq.setInt(path, 1)
        elif daq.getInt(path) == 1:
            daq.setInt(path, 0)


def set_integration_weights(
    daq,
    device,
    weights,
    channel,
    quadrature="real",
    demod_frequency=None
):
    """
    Sets the integration weights of the UHFQA. The input signals 
    are multiplied with the integrtion weights for each channel.

    Arguments:
        daq (zhinst.ziDAQServer) -- Data Server Object
        device (String) -- device ID, e.g. "dev2266"
        weights (double) -- list of double describing the integration 
                              weights to be set, max. length is 4096
        channel (int) -- index of channel to set weights of 

    Keyword Arguments:
        quadrature (str) -- quadrature of weights to be set, 
                            either 'imag' or 'real' (default: 'real')
        demod_frequency (double) -- frequency for demodulation 
                                    (default: None)
    """

    monitor_length = daq.getInt(f"/{device}/qas/0/monitor/length")
    integration_length = len(weights)
    assert integration_length <= 4096
    assert channel in range(10)
    assert quadrature in ["real", "imag"]

    # if weight is only one point, set constant weight for total length
    if len(weights) == 1:
        weights = weights * np.ones(monitor_length)

    # set lengths to the same, smallest value
    if integration_length > monitor_length:
        weights = weights[:monitor_length]
        integration_length = monitor_length
    if integration_length < monitor_length:
        monitor_length = integration_length

    # generate weights for digital demodulation
    if demod_frequency is not None:
        demod_weights = generate_demod_weights(integration_length, demod_frequency)
    else:
        demod_weights = np.ones(integration_length)

    # generate weights
    integration_weights = weights * demod_weights

    # reset
    daq.setInt(f"/{device}/qas/0/integration/length", 4096)
    daq.setVector(
        f"/{device}/qas/0/integration/weights/{channel}/{quadrature}",
        np.zeros(4096),
    )
    # set 
    daq.setInt(f"/{device}/qas/0/integration/length", integration_length)
    daq.setVector(
        f"/{device}/qas/0/integration/weights/{channel}/{quadrature}",
        integration_weights,
    )


def reset_integration_weights(daq, device, channels=range(10)):
    """
    Resets the integration weights of the UHFQA to all zeros. 
    If no channel specified all are reset.

    Arguments:
        daq (zhinst.ziDAQServer) -- Data Server Object
        device (String) -- device ID, e.g. "dev2266"

    Keyword Arguments:
        channels (int) --  list of indeces of channels to be reset 
                             (default: range(10))
    """

    daq.setInt(f"/{device}/qas/0/integration/length", 4096)
    for ch in channels:
        daq.setVector(
            f"/{device}/qas/0/integration/weights/{ch}/real",
            np.zeros(4096),
        )
        daq.setVector(
            f"/{device}/qas/0/integration/weights/{ch}/imag",
            np.zeros(4096),
        )


def set_qa_results(daq, device, result_length, result_averages, source="integration"):
    """
    Applies settings to the QA Results tab.

    Arguments:
        daq (zhinst.ziDAQServer) -- Data Server Object
        device (String) -- device ID, e.g. "dev2266"
        result_length (int) --  number of samples to be recorded
        result_averages (int) -- number of averages for results

    Keyword Arguments:
        source (str) -- specifies data source of QA 
                        "integratio", "rotation" or "threshold" 
                        (default: "integration")
    """

    if source == "integration":
        source = 7
    elif source == "rotation":
        source = 2
    elif source == "threshold":
        source = 1

    settings = [
        ("qas/0/result/enable", 0),
        ("qas/0/result/reset", 1),
        ("qas/0/result/length", result_length),
        ("qas/0/result/averages", result_averages),
        ("qas/0/result/source", source),
        ("qas/0/result/enable", 1),
    ]
    daq.set([(f"/{device}/{node}", value) for node, value in settings])


def set_qa_monitor(daq, device, monitor_length, averages):
    """
    Applies settings to the QA Monitor tab.

    Arguments:
        daq (zhinst.ziDAQServer) -- Data Server Object
        device (String) -- device ID, e.g. "dev2266"
        monitor_length (int) -- number of samples recorded in monitor tab
        averages (int) -- number of averages for monitor tab
    """

    settings = [
        ("qas/0/monitor/enable", 0),
        ("qas/0/monitor/reset", 1),
        ("qas/0/monitor/length", monitor_length),
        ("qas/0/monitor/averages", averages),
        ("qas/0/monitor/enable", 1),
    ]
    daq.set([(f"/{device}/{node}", value) for node, value in settings])


def optimal_integration_weights(
    daq,
    device,
    awg,
    channel,
    frequencies,
    plot=False,
    delay=None,
):
    """
    Sets the optimal integration weights for specified channel. 
    Measures IQ traces for channel being in ground/excited state 
    and takes difference as optimal weights.

    Arguments:
        daq (zhinst.ziDAQServer) -- Data Server Object
        device (String) -- device ID, e.g. "dev2266"
        awg (awgModule) -- awgModule() Object of AWG
        channel (int) -- index of channel to set weights for
        frequencies (float) -- list of readout frequencies for all channels

    Keyword Arguments:
        plot (bool) -- if set, detailed plots are shown (default: False)
        delay (int) -- number of samples at the beginning of weights array 
                       that are set to 0 (default: None)
    """

    
    daq.flush()
    monitor_length = daq.getInt(f"/{device}/qas/0/monitor/length")
    monitor_averages = daq.getInt(f"/{device}/qas/0/monitor/averages")

    reset_integration_weights(daq, device, channels=[channel])
    monitor_paths = [
        f"/{device}/qas/0/monitor/inputs/0/wave",
        f"/{device}/qas/0/monitor/inputs/1/wave",
    ]

    monitor_list = []
    
    ground_state = [0]
    excited_state = [1]
    
    for state in [ground_state, excited_state]: 
        print(f"Channel {channel} in state |{','.join(str(num) for num in state)}>", flush=True)
        # set up AWG sequence program
        # readout pulse for only single channel!
        awg_program = sequence_multiplexed_readout(
            [channel],
            frequencies,
            monitor_averages,
            state=state
        )
        compile_sequence(awg, awg_program)

        # ensure all settings are synced and subscribe to monitor paths
        daq.sync()
        time.sleep(0.1)
        daq.subscribe(monitor_paths)

        # run AWG sequence and start acquisition
        run_awg(daq, device)

        # poll data
        monitor_list.append(acquisition_poll(daq, monitor_paths, monitor_length))
        print("\t\t--> Data acquired")

        # unsubscribe immediately after aquisition!
        daq.unsubscribe(monitor_paths)

    waves = []
    for polldata in monitor_list:
        for path, data in polldata.items():
            waves.append(data)

    wave_I_0 = waves[0]
    wave_Q_0 = waves[1]
    wave_I_1 = waves[2]
    wave_Q_1 = waves[3]

    weights_I = wave_I_1 - wave_I_0
    weights_Q = wave_Q_1 - wave_Q_0
    weights_I = weights_I / np.max(np.abs(weights_I))
    weights_Q = weights_Q / np.max(np.abs(weights_Q))

    if delay is not None:
        weights_I[:delay] = 0
        weights_Q[:delay] = 0

    set_integration_weights(
        daq, device, weights_I, channel, quadrature="real"
    )
    set_integration_weights(
        daq, device, weights_Q, channel, quadrature="imag"
    )

    if plot:
        # set up plot
        fig, (ax1, ax2, ax3) = plt.subplots(3, figsize=[10, 8])

        ax1.grid("on")
        ax1.plot(wave_I_0, label="Input I", color=plt.cm.tab20(0))
        ax1.plot(wave_Q_0, label="Input Q", color=plt.cm.tab20(1))
        ax1.legend(frameon=False, loc=3)
        ax1.set_title("Qubit in ground state", position=[0.15, 0.7])
        ax1.set_xlim([0, monitor_length])

        ax2.grid("on")
        ax2.plot(wave_I_1, label="Input I", color=plt.cm.tab20(0))
        ax2.plot(wave_Q_1, label="Input Q", color=plt.cm.tab20(1))
        ax2.legend(frameon=False, loc=3)
        ax2.set_title("Qubit in excited state", position=[0.15, 0.7])
        ax2.set_xlim([0, monitor_length])

        ax3.axvline(delay, c="k", linewidth=0.5)
        ax3.grid("on")
        ax3.plot(weights_I, label="Weight I", color=plt.cm.tab20(0))
        ax3.plot(weights_Q, label="Weight Q", color=plt.cm.tab20(1))
        ax3.legend(frameon=False, loc=3)
        ax3.set_title("Integration weights for I/Q", position=[0.15, 0.7])
        ax3.set_xlim([0, monitor_length])
        ax3.set_xlabel("Samples")
        
        plt.show()


def acquisition_poll(daq, paths, num_samples, timeout=10.0):
    """ Polls the UHFQA for data. Taken from zhinst.examples.uhfqa.common

    Args:
        paths (list): list of subscribed paths
        num_samples (int): expected number of samples
        timeout (float): time in seconds before timeout Error is raised.
    """
    poll_length = 0.001  # s
    poll_timeout = 500  # ms
    poll_flags = 0
    poll_return_flat_dict = True

    # Keep list of recorded chunks of data for each subscribed path
    chunks = {p: [] for p in paths}
    gotem = {p: False for p in paths}

    # Poll data
    time = 0
    while time < timeout and not all(gotem.values()):
        dataset = daq.poll(poll_length, poll_timeout, poll_flags, poll_return_flat_dict)
        for p in paths:
            if p not in dataset:
                continue
            for v in dataset[p]:
                chunks[p].append(v['vector'])
                num_obtained = sum([len(x) for x in chunks[p]])
                if num_obtained >= num_samples:
                    gotem[p] = True
        time += poll_length

    if not all(gotem.values()):
        for p in paths:
            num_obtained = sum([len(x) for x in chunks[p]])
            print('Path {}: Got {} of {} samples'.format(p, num_obtained, num_samples))
        raise Exception('Timeout Error: Did not get all results within {:.1f} s!'.format(timeout))

    # Return dict of flattened data
    return {p: np.concatenate(v) for p, v in chunks.items()}



if __name__ == "__name__":
    pass
